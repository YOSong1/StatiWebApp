import pandas as pd
from pyDOE2 import fullfact, fracfact, pbdesign, bbdesign, ccdesign


class DesignController:
    """DOE 설계 생성을 담당하는 컨트롤러"""

    def __init__(self, parent=None):
        self.parent = parent

    # 요인 설계 ------------------------------------------------------------
    def create_full_factorial(self, levels):
        """
        일반 다수준 요인설계 생성.
        levels: 각 요인의 수준 수 리스트 (예: [2, 3, 2])
        """
        design = fullfact(levels)
        columns = [f"F{i+1}" for i in range(len(levels))]
        df = pd.DataFrame(design, columns=columns)
        return df.astype(int)

    def create_fractional_factorial(self, design_str):
        """
        2수준 부분요인 설계 생성.
        design_str: pyDOE2 generator 문자열 (예: 'a b ab')
        """
        design = fracfact(design_str)
        columns = [f"F{i+1}" for i in range(design.shape[1])]
        df = pd.DataFrame(design, columns=columns)
        return df.astype(int)

    def create_plackett_burman(self, factors):
        """Plackett-Burman 설계 생성"""
        design = pbdesign(factors)
        columns = [f"F{i+1}" for i in range(design.shape[1])]
        df = pd.DataFrame(design, columns=columns)
        return df.astype(int)

    # 반응표면 설계 --------------------------------------------------------
    def create_box_behnken(self, factors, center=1):
        """Box-Behnken 설계 생성 (요인 3개 이상 권장)"""
        if factors < 3:
            raise ValueError("Box-Behnken 설계는 최소 3개 이상의 요인이 필요합니다.")
        design = bbdesign(factors, center=center)
        columns = [f"F{i+1}" for i in range(design.shape[1])]
        return pd.DataFrame(design, columns=columns)

    def create_ccd(self, factors, center=(4, 4), alpha="orthogonal"):
        """중심합성설계(CCD) 생성"""
        # face를 명시적으로 지정하지 않으면 pyDOE2에서 None.lower() 에러가 날 수 있어 "ccc"로 강제
        design = ccdesign(factors, center=center, alpha=alpha, face="ccc")
        columns = [f"F{i+1}" for i in range(design.shape[1])]
        return pd.DataFrame(design, columns=columns)

    # 직교배열/Taguchi ------------------------------------------------------
    def create_orthogonal_array(self, factors, design="L8"):
        """간단한 직교배열(Taguchi) 생성: L4/L8/L9 지원"""
        design = design.upper()
        taguchi_tables = {
            "L4": [
                [1, 1, 1],
                [1, 2, 2],
                [2, 1, 2],
                [2, 2, 1],
            ],
            "L8": [
                [1, 1, 1, 1, 1, 1, 1],
                [1, 1, 1, 2, 2, 2, 2],
                [1, 2, 2, 1, 1, 2, 2],
                [1, 2, 2, 2, 2, 1, 1],
                [2, 1, 2, 1, 2, 1, 2],
                [2, 1, 2, 2, 1, 2, 1],
                [2, 2, 1, 1, 2, 2, 1],
                [2, 2, 1, 2, 1, 1, 2],
            ],
            "L9": [
                [1, 1, 1, 1],
                [1, 2, 2, 2],
                [1, 3, 3, 3],
                [2, 1, 2, 3],
                [2, 2, 3, 1],
                [2, 3, 1, 2],
                [3, 1, 3, 2],
                [3, 2, 1, 3],
                [3, 3, 2, 1],
            ],
        }

        if design not in taguchi_tables:
            raise ValueError(f"지원하지 않는 직교배열입니다: {design}")

        table = pd.DataFrame(taguchi_tables[design], dtype=int)
        if factors > table.shape[1]:
            raise ValueError(f"{design} 설계는 최대 {table.shape[1]}개 요인까지 지원합니다.")

        table = table.iloc[:, :factors]
        table.columns = [f"F{i+1}" for i in range(table.shape[1])]
        return table
