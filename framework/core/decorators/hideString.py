from functools import wraps

def hide(pattern: str = "*", dict_keys: list = None, array_positions: list = None):
    """
    Decorator to hide data selectively.
    
    pattern: "*" or "*N" → string masking
    dict_keys: list of keys to mask in dictionaries
    array_positions: list of indices to mask in arrays/lists
    """

    # ---------------------
    # Mask string
    # ---------------------
    def mask_string(s: str) -> str:
        if pattern == "*":
            return "*" * len(s)
        elif pattern.startswith("*") and pattern[1:].isdigit():
            n = int(pattern[1:])
            if n >= len(s):
                return s
            return "*" * (len(s) - n) + s[-n:]
        return s

    # ---------------------
    # Mask array/list
    # ---------------------
    def mask_array(arr: list) -> list:
        masked = []
        for i, v in enumerate(arr):
            if array_positions is None or i in array_positions:
                masked.append(mask_data(v))
            else:
                masked.append(v)
        return masked

    # ---------------------
    # Mask dict
    # ---------------------
    def mask_dict(d: dict) -> dict:
        masked = {}
        for k, v in d.items():
            if dict_keys is None or k in dict_keys:
                masked[k] = mask_data(v)
            else:
                masked[k] = v
        return masked

    # ---------------------
    # Recursive data mask
    # ---------------------
    def mask_data(data):
        if isinstance(data, str):
            return mask_string(data)
        elif isinstance(data, list):
            return mask_array(data)
        elif isinstance(data, tuple):
            return tuple(mask_array(list(data)))
        elif isinstance(data, dict):
            return mask_dict(data)
        else:
            return data

    # ---------------------
    # Decorator wrapper
    # ---------------------
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return mask_data(result)
        return wrapper
    return decorator


'''
class TestData:

    @staticmethod
    @hide("*4")
    def hide_string():
        return "SensitiveString"

    @staticmethod
    @hide(array_positions=[1])
    def hide_array():
        return ["keep1", "hide2", "keep3"]

    @staticmethod
    @hide(dict_keys=["password", "token"])
    def hide_dict():
        return {
            "username": "user123",
            "password": "supersecret",
            "token": "abcdef123456",
            "email": "user@example.com"
        }

print("Masked string:", TestData.hide_string())
print("Masked array:", TestData.hide_array())
print("Masked dict:", TestData.hide_dict())

Masked string: ************ring
Masked array: ['keep1', '****', 'keep3']
Masked dict: {'username': 'user123', 'password': '***********', 'token': '************', 'email': 'user@example.com'}


'''