import torch
from transformers import AutoModelForCausalLM, GPT2Config, GPT2Model, GPT2Tokenizer, pipeline

from config import config
from models.model_base import ModelBase

PRE_TRAINED_MODEL = 'gpt2'


class GPT2(ModelBase):

    def __init__(self, storage_manager, model_name, pipeline_name, use_trained_model=False, is_inference_mode=False):
        self.pipeline_name = pipeline_name
        self.pipeline = None
        self.tokenizer = None
        super(GPT2, self).__init__(model_name, storage_manager, use_trained_model, is_inference_mode)

    def _do_create_model_config(self):
        return GPT2Config.from_pretrained(PRE_TRAINED_MODEL)

    def _do_create_model(self, model_config):
        # for text generation, we need a GPT2 model with a language model head: the easiest way to instantiate the
        # correct model is to grab it from the pipeline
        if self.pipeline_name is not None:
            model = AutoModelForCausalLM.from_pretrained(PRE_TRAINED_MODEL,
                                                         config=model_config,
                                                         _from_pipeline=self.pipeline_name,
                                                         ignore_mismatched_sizes=True)
            self.tokenizer = GPT2Tokenizer.from_pretrained(PRE_TRAINED_MODEL, config=model_config)
            self.pipeline = pipeline(self.pipeline_name, model=model, tokenizer=self.tokenizer)
            return model
        else:
            self.tokenizer = GPT2Tokenizer.from_pretrained(PRE_TRAINED_MODEL, config=model_config)
            return GPT2Model.from_pretrained(PRE_TRAINED_MODEL,
                                             config=model_config,
                                             ignore_mismatched_sizes=True)

    def _do_load_model(self, model_config):
        self.tokenizer = GPT2Tokenizer.from_pretrained(PRE_TRAINED_MODEL, config=model_config)
        return GPT2Model.from_pretrained(self.get_model_path())

    def get_save_model_in_folder(self):
        return True

    def save_model(self):
        if self.model is None:
            return
        self.model.save_pretrained(self.get_model_path())

    def tokenize(self, prompt_text, return_tensors=False):
        encoded_input = self.tokenizer(prompt_text,
                                       padding=False,
                                       add_special_tokens=False,
                                       return_tensors=return_tensors).data
        if return_tensors == 'pt':
            for key in encoded_input:
                encoded_input[key] = encoded_input[key].to(self.get_device_type())
        return encoded_input

    def forward(
            self,
            input_ids=None,
            past_key_values=None,
            attention_mask=None,
            token_type_ids=None,
            position_ids=None,
            head_mask=None,
            inputs_embeds=None,
            labels=None,
            use_cache=None,
            output_attentions=None,
            output_hidden_states=None,
            return_dict=None):
        return self.get_model()(input_ids=input_ids,
                                past_key_values=past_key_values,
                                attention_mask=attention_mask,
                                token_type_ids=token_type_ids,
                                position_ids=position_ids,
                                head_mask=head_mask,
                                inputs_embeds=inputs_embeds,
                                labels=labels,
                                use_cache=use_cache,
                                output_attentions=output_attentions,
                                output_hidden_states=output_hidden_states,
                                return_dict=return_dict)

    def _do_train_model(self):
        raise Exception("Use the Trainer for this model instead of calling train_model()")

    def _do_update_model(self, message_ids):
        pass

    def set_eval_mode(self):
        super().set_eval_mode()

    def validate_model(self):
        pass

    @torch.no_grad()
    def predict(self, input):
        self.set_eval_mode()
        # extracted from TextGenerationPipeline in transformers/pipelines.py so I can play with the inner workings
        if self.pipeline_name == 'text-generation':
            encoded_input = self.tokenize(input, return_tensors=config.framework)
            input_ids = encoded_input["input_ids"]
            attention_mask = encoded_input.get("attention_mask", None)
            # Allow empty prompts
            if input_ids.shape[1] == 0:
                input_ids = None
                attention_mask = None
                in_b = 1
            else:
                in_b = input_ids.shape[0]
            model_outputs = self.model.generate(input_ids=input_ids,
                                                attention_mask=attention_mask,
                                                max_new_tokens=config.response_max_tokens)
            out_b = model_outputs.shape[0]
            generated_sequence = model_outputs.reshape(in_b, out_b // in_b, *model_outputs.shape[1:])
            model_outputs = {'generated_sequence': generated_sequence, 'input_ids': input_ids, 'prompt_text': input}
            response = self.postprocess(model_outputs)
            return response
        elif self.pipeline is not None:
            return self.pipeline(input)
        else:
            raise Exception("No pipeline defined")

    @torch.no_grad()
    def predict_batch(self, prompt_texts):
        """returns a list of predictions (predicted_class_name, probability, probabilities) for the input messages"""
        self.set_eval_mode()
        encoded_input = self.tokenize(prompt_texts, return_tensors=config.framework)
        input_ids = encoded_input["input_ids"]
        attention_mask = encoded_input.get("attention_mask", None)
        # Allow empty prompts
        if input_ids.shape[1] == 0:
            input_ids = None
            attention_mask = None
            in_b = 1
        else:
            in_b = input_ids.shape[0]
        model_outputs = self.generate(input_ids=input_ids, attention_mask=attention_mask)
        out_b = model_outputs.shape[0]
        generated_sequence = model_outputs.reshape(in_b, out_b // in_b, *model_outputs.shape[1:])
        response = self.postprocess(generated_sequence)
        return response

    def postprocess(self, model_outputs):
        generated_sequence = model_outputs['generated_sequence'][0].numpy().tolist()
        input_ids = model_outputs["input_ids"]
        prompt_text = model_outputs["prompt_text"]
        responses = []
        for sequence in generated_sequence:
            # decode text
            text = self.tokenizer.decode(
                sequence,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )
            if input_ids is None:
                prompt_length = 0
            else:
                prompt_length = len(
                    self.tokenizer.decode(
                        input_ids[0],
                        skip_special_tokens=True,
                        clean_up_tokenization_spaces=True,
                    )
                )
            text = text[prompt_length:]
            responses.append(text)
        return len(responses) == 1 and responses[0] or responses
