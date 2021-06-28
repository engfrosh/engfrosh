class FroshTeam:
    def __init__(self, id: int, display_name: str, coin_amount: int = None) -> None:
        self.id = id
        self.name = display_name
        self.coin = coin_amount
