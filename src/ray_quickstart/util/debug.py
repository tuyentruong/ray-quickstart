from ray import logger


def inspect_ray_serializability(obj):
    """
    Check serializability of an object using Ray's inspect_serializability function.
    Please note that there is currently an issue with pickling when the multiprocessing module is imported
    """
    from ray.util import inspect_serializability
    for attribute, value in obj.__dict__.items():
        logger.info(f'inspecting serializability of {attribute}...')
        inspect_serializability(value)
