import datetime as dt

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

def validate_activity(is_scoreable: bool, 
                      max_score: int | None, 
                      start_dt: dt.datetime | None, 
                      end_dt: dt.datetime | None) -> None:
        # Если активность "на очки", у нее должна быть максимальная оценка
        if is_scoreable and max_score is None:
            raise ValueError("max_score is required when activity is scoreable")

        # Если это просто событие (не на очки), у него должны быть даты начала и конца
        if not is_scoreable and (start_dt is None or end_dt is None):
            raise ValueError("start_dt and end_dt are required when activity is not scoreable")

        # Дата начала должна быть раньше даты конца
        if start_dt and end_dt and start_dt >= end_dt:
            raise ValueError("start_dt must be earlier than end_dt")