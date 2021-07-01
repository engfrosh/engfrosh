class FroshTeam:
    def __init__(self, id: int, display_name: str, coin_amount: int = None) -> None:
        self.id = id
        self.name = display_name
        self.coin = coin_amount


class ScavQuestion:
    def __init__(self, id: int, enabled: bool, identifier: str, text: str, weight: int,
                 answer: str) -> None:

        self.id = id
        self.enabled = enabled
        self.identifier = identifier
        self.text = text
        self.weight = weight
        self.answer = answer
