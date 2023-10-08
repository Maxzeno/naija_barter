def validate_alphanumeric_password(value):
    return any(char.isalpha() for char in value) and any(char.isdigit() for char in value)
