import subprocess


class Transmittance(object):
    """Calculate the transmittance of a stratigraphy with material
    in series or in parallel.

    The stratigraphy is described by a pattern with the following conventions:
    * comma separated values: materials in series
    * double-slash separetd values: material in parallel
    * comma separated values in brackets: material in series within parallel
    For instance:
    pattern = "1,(2,3,4)//5//(6,7),8"

    The indexes used in the pattern (n) are different from the ones used to
    identify different materials (id).
    For instance:
    pattern = "1,2,3"
    stratigraphy = {
        "1": {"mat": 1, "thk": 1, "area": 1, "cnd": .01},
        "2": {"mat": 2, "thk": 1, "area": 1, "rst": .02},
        "3": {"mat": 1, "thk": 1, "area": 1, "cnd": .01}
        }
    where:
    "mat": material
    "thk": thickness
    "area"
    "cnd": conducttivity
    "rst": resistance
    """
    def __init__(self, pattern, strat, area):
        self.transmittance = 1 / self.resistance(pattern, strat, area)
        print(self.transmittance)

    def resistance(self, pattern, strat, area):
        """Calculate the resistance of a given pattern of a stratigraphy.

        :param pattern (str): sequence of indexes in series or in parallel
        :param strat (dict): info relative to each material in the pattern
        :param area (float): tot surface of the stratigraphy
        :return resistante (flot): the resistance [(m^2 K)/W]
        """
        pattern = pattern.replace(" ", "")
        pattern = self.split_series(pattern)

        # calc the resistance of the structure
        rst = []
        for i in pattern:
            i = i.split("//")
            if len(i) > 1:  # indexes in parallel
                p_rst = []
                for p in i:
                    p = p.strip("()").split(",")
                    if len(p) > 1:  # indexes in series in parallel
                        s_rst = []
                        for s in p:
                            s_rst.append(self.rst_material(strat, s))
                        p_rst.append(1 / sum(s_rst))
                    else:
                        p_rst.append(1 / self.rst_material(strat, p[0]))
                rst.append(1 / sum(p_rst))
            else:
                rst.append(self.rst_material(strat, i[0]))
        tot_rst = sum(rst) * area  # (m^2 K)/W
        return tot_rst

    def split_series(self, pattern):
        """Split the pattern into indexes in series.

        For instance:
        "1,(2,3,4)//5//(6,7),8"
        is splitted in:
        ["1", "(2,3,4)//5//(6,7)", "8"]

        :param pattern (str): sequence of indexes in series or in parallel
        :return series (list): (chunk of) indexes in series in the pattern
        """
        series = []
        n = ""  # indexes used in the pattern
        inparallel = 0
        for i, v in enumerate(pattern):
            if v == "," and inparallel == 0:
                series.append(n)
                n = ""
            elif v == "(":
                inparallel = 1
                n = n + str(v)
            elif v == ")" and pattern[i+1] == ",":
                inparallel = 0
                n = n + str(v)
            elif i == len(pattern) - 1:
                n = n + str(v)
                series.append(n)
            else:
                n = n + str(v)
        return series

    def rst_material(self, strat, n):
        """Return the resistence of a given material.

        :param strat (dict): info relative to each material in the pattern
        :param n (str): position of a given material in the pattern
        :return rst (float): the resistance
        """
        rst = 0
        if "cnd" in strat[n]:
            rst = strat[n]["thk"] / strat[n]["cnd"]  # (m^2 K)/W
        else:
            rst = strat[n]["rst"]  # (m^2 K)/W
        rst = rst / strat[n]["area"]  # K/W
        strat[n]["rst/area"] = "{:.3f}".format(rst)  # 3 deciamls
        return rst


class Latex(Transmittance):
    """Write the LaTex document."""
    def __init__(self, pattern, strat, area, filename, lang):
        super().__init__(pattern, strat, area)

        preamble = self.preamble(lang)
        table = self.table_results(strat)
        with open(filename, "w") as f:
            f.write("\n".join(preamble))
            f.write("\n\\begin{document}\n\n")
            f.write("\n".join(table))
            f.write("\n\n\\end{document}")
            f.closed

    def preamble(self, lang):
        """Preamble.

        :param lang (str): language to use for babel package
        :return preamble (list): the preamble
        """
        preamble = ["\\documentclass[10pt,a4paper]{article}",
                    "\\usepackage[utf8]{inputenc}",
                    "\\usepackage[{}]{{babel}}".format(lang),
                    "\\usepackage{amsmath}",
                    "\\usepackage{amsfonts}",
                    "\\usepackage{amssymb}",
                    "\\usepackage{graphicx}",
                    "\\usepackage[left=2cm,right=2cm,"
                    "top=2cm,bottom=2cm]{geometry}",
                    "\\usepackage{caption}",
                    "\\usepackage{siunitx}"]
        return preamble

    def table_results(self, strat):
        """Table results of the stratigraphy.

        :param strat (dict): info relative to each material in the pattern
        :return table (list): the table
        """
        data = []
        for i in sorted(strat.keys()):
            cdata = []
            cdata.extend([i, str(strat[i]['mat']), str(strat[i]['thk'])])
            if "cnd" in strat[i]:
                cdata.append(str(strat[i]['cnd']) + " &")
            else:
                cdata.append("& " + str(strat[i]['rst']))
            cdata.extend([str(strat[i]['area']), str(strat[i]['rst/area'])])
            data.append(" & ".join(cdata) + " \\\\")

        table = ["\\begin{table}[ht]",
                 "\\centering",
                 "\\begin{tabular}{c|cccccc|ccc}",
                 "& "
                 "& "
                 "[m] & "
                 "$\left[\dfrac{W}{(K \cdot m)}\\right]$ & "
                 "$\left[\dfrac{(m^2 \cdot K)}{W}\\right]$ & "
                 "[$m^2$] & "
                 "$\left[\dfrac{K}{W}\\right]$ & "
                 "[$m^2$] & "
                 "$\left[\dfrac{(m^2 \cdot K)}{W}\\right]$ & "
                 "$\left[\dfrac{W}{(m^2 \cdot K)}\\right]$ \\\\",
                 "n & "
                 "id & "
                 "$s_i$ & "
                 "$\lambda_i$ & "
                 "$R_i$ & "
                 "$A_i$ & "
                 "$R_i/A_i$ & "
                 "$A$ & "
                 "$R$ & "
                 "$K$ \\\\",
                 "\\hline",
                 "\\hline",
                 "\\end{tabular}",
                 "\\end{table}"]
        table[-3:1] = data
        return table


def test():
    pattern = "1, (2,3,4)//5//(6,7), 8"
    strat = {
        "1": {"mat": 1, "thk": 1, "area": 3, "cnd": .1},
        "2": {"mat": 2, "thk": 1, "area": 1, "rst": .2},
        "3": {"mat": 3, "thk": 1, "area": 1, "cnd": .3},
        "4": {"mat": 2, "thk": 1, "area": 1, "rst": .4},
        "5": {"mat": 4, "thk": 3, "area": 1, "cnd": .5},
        "6": {"mat": 3, "thk": 1.5, "area": 1, "cnd": .6},
        "7": {"mat": 2, "thk": 1.5, "area": 1, "rst": .7},
        "8": {"mat": 1, "thk": 1, "area": 3, "cnd": .8}
    }
    area = 3
    filename = "testThStrat.tex"
    lang = "english"

    Latex(pattern, strat, area, filename, lang)
    subprocess.run(["pdflatex", filename])


if __name__ == "__main__":
    test()
