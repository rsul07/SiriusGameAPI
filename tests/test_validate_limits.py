import pytest
from helpers.validators import validate_limits


# Корректные случаи
@pytest.mark.parametrize("is_team,max_members,max_teams", [
    (False, 10, None),
    (True, 12, 3),  # 12 делится на 3
    (True, 6, 2),  # 6 делится на 2
])
def test_validate_limits_ok(is_team, max_members, max_teams):
    validate_limits(is_team, max_members, max_teams)


# Некорректные случаи
@pytest.mark.parametrize("is_team,max_members,max_teams,err", [
    (False, None, None, "max_members must be a positive integer"),
    (False, 0, None, "max_members must be a positive integer"),
    (False, 5, 2, "max_teams not allowed when is_team=False"),
    (True, 10, None, "max_teams required when is_team=True"),
    (True, 10, 0, "max_teams must be a positive integer"),
    (True, 10, 3, "max_members must be divisible by max_teams"),
])
def test_validate_limits_fail(is_team, max_members, max_teams, err):
    with pytest.raises(ValueError) as exc:
        validate_limits(is_team, max_members, max_teams)
    assert err in str(exc.value)
