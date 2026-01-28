from __future__ import annotations

import pandas as pd

from controllers.design_controller import DesignController


class DesignService:
    def __init__(self):
        self._controller = DesignController()

    def full_factorial(self, levels: list[int]) -> pd.DataFrame:
        return self._controller.create_full_factorial(levels)

    def fractional_factorial(self, design_str: str) -> pd.DataFrame:
        return self._controller.create_fractional_factorial(design_str)

    def plackett_burman(self, factors: int) -> pd.DataFrame:
        return self._controller.create_plackett_burman(factors)

    def box_behnken(self, factors: int, center: int = 1) -> pd.DataFrame:
        return self._controller.create_box_behnken(factors, center=center)

    def ccd(self, factors: int, center: tuple[int, int] = (4, 4), alpha: str = "orthogonal") -> pd.DataFrame:
        return self._controller.create_ccd(factors, center=center, alpha=alpha)

    def orthogonal_array(self, factors: int, design: str = "L8") -> pd.DataFrame:
        return self._controller.create_orthogonal_array(factors, design=design)
