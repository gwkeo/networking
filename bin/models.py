class Settings:

    def __init__(self, tables_count: int, seats_count: int, round_time: int, break_time: int = 1):
        self.tables_count = tables_count
        self.seats_count = seats_count
        self.round_time = round_time
        self.break_time = break_time