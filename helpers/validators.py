def validate_limits(is_team: bool, 
                    max_members: int | None,
                    max_teams: int | None) -> None:
    if not isinstance(max_members, int) or max_members <= 0:
        raise ValueError("max_members must be a positive integer")
    
    if is_team:
        if max_teams is None:
            raise ValueError("max_teams required when is_team=True")
        elif not isinstance(max_teams, int) or max_teams <= 0:
            raise ValueError("max_teams must be a positive integer")
        elif max_members % max_teams != 0:
            raise ValueError("max_members must be divisible by max_teams")
    else:
        if max_teams is not None:
            raise ValueError("max_teams not allowed when is_team=False")