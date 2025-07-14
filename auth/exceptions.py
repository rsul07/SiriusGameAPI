class UserAlreadyExistsError(Exception):
    """Выбрасывается, когда пользователь с таким email или телефоном уже существует."""
    pass
