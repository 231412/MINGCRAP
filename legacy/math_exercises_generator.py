import os, docx
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

doc = Document()

# 设置默认字体
style = doc.styles['Normal']
font = style.font
font.name = '微软雅黑'
font.size = Pt(11)

# 设置页边距
for section in doc.sections:
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

# 标题
title = doc.add_heading('', level=0)
run = title.add_run('数学练习题汇编')
run.font.size = Pt(22)
run.font.color.rgb = RGBColor(0, 51, 102)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# 副标题
subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run('因式分解 · 一元二次方程 · 二次函数 · 几何')
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(100, 100, 100)

doc.add_paragraph()  # 空行

# ========== 第一部分：因式分解 ==========
h1 = doc.add_heading('', level=1)
run = h1.add_run('一、因式分解（8天，每天10道）')
run.font.color.rgb = RGBColor(0, 51, 102)

factor_data = [
    # 第1天
    ["x²+5x+6", "x²-7x+12", "x²+2x-15", "2x²+7x+3", "3x²-11x+6",
     "x²-9", "4x²-12x+9", "x³+x²+x+1", "x³-2x²+x-2", "x²+4xy+4y²"],
    # 第2天
    ["x²+8x+15", "x²-2x-24", "x²-6x+9", "2x²+3x-2", "6x²-5x-6",
     "9x²-16y²", "2x³-2x²+x-1", "x³-3x²+2x-6", "5x²-20", "a²-4ab+4b²"],
    # 第3天
    ["x²+10x+21", "x²-3x-18", "x²-14x+49", "3x²+8x+5", "4x²-4x-15",
     "25x²-1", "4x²+20x+25", "x³+2x²+3x+6", "2x³-x²+6x-3", "x²-2xy-3y²"],
    # 第4天
    ["x²-9x+14", "x²+4x-12", "x²-16", "5x²+14x-3", "2x²-7x-15",
     "16x²-8x+1", "9x²-4y²", "x³-x²+x-1", "3x³+x²+3x+1", "x²+5xy+6y²"],
    # 第5天
    ["x²+3x-40", "x²-11x+30", "x²-10x+25", "7x²+6x-1", "3x²+2x-8",
     "4x²-20x+25", "36x²-49y²", "x³+3x²-2x-6", "2x³+3x²+2x+3", "x²-2xy-8y²"],
    # 第6天
    ["x²-5x-24", "x²+6x-27", "x²-8x+16", "2x²+5x-3", "6x²+x-12",
     "25x²-30x+9", "49x²-64", "x³-2x²-x+2", "4x³+2x²+2x+1", "4x²-12xy+9y²"],
    # 第7天
    ["x²-2x-35", "x²+7x-18", "x²-20x+100", "3x²-5x-12", "8x²+10x-3",
     "9x²+12x+4", "16x²-81", "x³+4x²-x-4", "5x³-x²+5x-1", "x²+6xy+8y²"],
    # 第8天
    ["x²+9x-22", "x²-13x+36", "x²-4x+4", "5x²+9x-2", "7x²-8x-12",
     "9x²-6x+1", "64x²-25y²", "x³-3x²-4x+12", "2x³-5x²+2x-5", "x²+6xy+9y²"]
]

for day_idx, problems in enumerate(factor_data, 1):
    h2 = doc.add_heading('', level=2)
    run = h2.add_run(f'第{day_idx}天')
    run.font.color.rgb = RGBColor(0, 76, 153)
    
    # 两列布局
    table = doc.add_table(rows=5, cols=2)
    table.style = 'Table Grid'
    
    for i in range(5):
        for j in range(2):
            idx = i + j * 5
            cell = table.cell(i, j)
            cell.text = f'{idx+1}.  {problems[idx]}'
            for paragraph in cell.paragraphs:
                paragraph.style.font.size = Pt(11)
    
    doc.add_paragraph()  # 空行

# ========== 第二部分：一元二次方程 ==========
doc.add_page_break()
h1 = doc.add_heading('', level=1)
run = h1.add_run('二、一元二次方程含参大题（共16道）')
run.font.color.rgb = RGBColor(0, 51, 102)

eq_problems = [
    "1. 已知关于 x 的方程 x²-(2m+1)x+m²+m=0。\n   (1) 求证：该方程总有两个不相等的实数根；\n   (2) 若两根为 x₁,x₂，且 x₁²+x₂²=13，求 m。",
    "2. 已知关于 x 的方程 x²+2(k-1)x+k²-3=0 有两个实数根 x₁,x₂。\n   (1) 求 k 的取值范围；\n   (2) 若 x₁²+x₂²=6，求 k。",
    "3. 已知关于 x 的方程 x²-(m+2)x+2m=0。\n   (1) 求证：无论 m 取何值，方程总有实数根；\n   (2) 若两根互为相反数，求 m。",
    "4. 已知关于 x 的方程 x²+mx+m-1=0。\n   (1) 若方程有一个根为 -1，求 m 和另一个根；\n   (2) 若两根的平方和为 3，求 m。",
    "5. 已知关于 x 的方程 x²-(2k+1)x+k²+k=0 的两根为 x₁,x₂，且 x₁/x₂ + x₂/x₁ = 5/2，求 k。",
    "6. 已知关于 x 的方程 2x²-(3k+1)x+k²-2=0 有两个相等的实数根，求 k 的值及方程的根。",
    "7. 已知关于 x 的方程 x²+(2a-1)x+a²-a=0。\n   (1) 求证：该方程有两个实数根；\n   (2) 若两根的平方和等于 11，求 a。",
    "8. 已知关于 x 的方程 x²-(2m+3)x+m²+3m+2=0。\n   (1) 求证：该方程有两个不相等的实数根；\n   (2) 若两根的倒数和为 -1/2，求 m。",
    "9. 已知关于 x 的方程 x²+(m-3)x-m=0 的两根为 x₁,x₂，且 |x₁-x₂|=5，求 m。",
    "10. 已知关于 x 的方程 x²-(k+1)x+k=0。\n    (1) 当 k 为何值时，方程有两个相等的实数根；\n    (2) 若两根的立方和为 7，求 k。",
    "11. 已知关于 x 的方程 x²-(2m+1)x+m²+m=0 的两根分别为直角三角形两直角边的长，斜边为 5，求 m 和两直角边。",
    "12. 已知关于 x 的方程 x²-2mx+m²-4=0 的两个根为 x₁,x₂，若以 x₁,x₂ 为边长的矩形面积为 5，求 m。",
    "13. 已知关于 x 的方程 x²-2(k-1)x+k²-2k+1=0 有两个实数根 x₁,x₂，且 x₁²+x₂²=10，求 k。",
    "14. 已知关于 x 的方程 x²-(m+1)x+m-2=0，若两根均为正数，求 m 的取值范围。",
    "15. 已知关于 x 的方程 x²-3x+2k=0 的两个根为 x₁,x₂，且 x₁,x₂ 是一个直角三角形两条直角边的长，斜边为 √5，求 k 及两根。",
    "16. 已知关于 x 的方程 x²-(2k+1)x+k²-2k+3=0 有两个实数根 x₁,x₂，且 x₁x₂-x₁-x₂=5，求 k。"
]

for prob in eq_problems:
    p = doc.add_paragraph()
    run = p.add_run(prob)
    run.font.size = Pt(11)
    p.paragraph_format.space_after = Pt(6)

# ========== 第三部分：二次函数 ==========
doc.add_page_break()
h1 = doc.add_heading('', level=1)
run = h1.add_run('三、二次函数（15道）')
run.font.color.rgb = RGBColor(0, 51, 102)

quad_problems = [
    "1. 已知二次函数 y=x²-4x+1，求顶点坐标、对称轴、开口方向及最小值。",
    "2. 已知二次函数 y=-2x²+8x-5，求顶点坐标及最大值。",
    "3. 已知二次函数 y=2x²-6x+3，求在区间 [0,3] 上的最大值和最小值。",
    "4. 已知二次函数 y=-x²+4x-3，求在区间 [1,4] 上的最大值和最小值。",
    "5. 已知二次函数 y=x²-2x+3，将其图像向右平移2个单位、向上平移1个单位，求新抛物线解析式。",
    "6. 已知二次函数 y=ax²+bx+c 的顶点为 (1,-2)，且过点 (0,-1)，求该函数解析式。",
    "7. 已知二次函数 y=x²-(m+2)x+m，当 x=1 时取得最小值，求 m 及最小值。",
    "8. 已知二次函数 y=x²-4x+k 在区间 [-1,3] 上的最大值为 8，求 k。",
    "9. 已知二次函数 y=-x²+2x+3，求在区间 [0,2] 上的最大值和最小值，并写出对应 x 的值。",
    "10. 已知二次函数 y=x²+2ax+a²-1，求顶点坐标；当 a 为何值时，顶点在 x 轴上？",
    "11. 已知二次函数 y=2x²-4mx+m²-1 在区间 [-1,2] 上的最小值为 -3，求 m。",
    "12. 已知二次函数 y=x²-2x-3，求其图象与 x 轴的交点坐标，并写出 y 随 x 增大而增大时 x 的取值范围。",
    "13. 已知二次函数 y=ax²+bx+c 的图象经过点 (0,3),(1,0),(-1,6)，求解析式及顶点坐标。",
    "14. 已知二次函数 y=x²-2mx+m²+2m-1，求其最小值；当 m 为何值时，最小值为 3？",
    "15. 已知二次函数 y=-x²+2x+2，求在区间 [a,a+1] 上的最大值（用含 a 的式子表示）。"
]

for prob in quad_problems:
    p = doc.add_paragraph()
    run = p.add_run(prob)
    run.font.size = Pt(11)
    p.paragraph_format.space_after = Pt(6)

# ========== 第四部分：几何 ==========
doc.add_page_break()
h1 = doc.add_heading('', level=1)
run = h1.add_run('四、几何部分')
run.font.color.rgb = RGBColor(0, 51, 102)

# 直角三角形、相似
h2 = doc.add_heading('', level=2)
run = h2.add_run('直角三角形、相似三角形证明计算（20道）')
run.font.color.rgb = RGBColor(0, 76, 153)

geo_problems = [
    "1. 在 Rt△ABC 中，∠C=90°，AC=6，BC=8，求斜边 AB 上的高 CD。",
    "2. 在 Rt△ABC 中，∠C=90°，CD 是斜边 AB 上的高，已知 AD=4，BD=9，求 CD 和 AC。",
    "3. 在△ABC 中，DE∥BC，D 在 AB 上，E 在 AC 上，AD=2，DB=3，AE=4，求 EC。",
    "4. 在△ABC 中，DE∥BC，AD:DB=2:3，若 DE=6，求 BC。",
    "5. 在 Rt△ABC 中，∠ACB=90°，CD⊥AB 于 D，AC=3，BC=4，求 CD 和 BD。",
    "6. 已知△ABC∽△A'B'C'，相似比为 2:3，△ABC 的周长为 20，求△A'B'C' 的周长。",
    "7. 在△ABC 中，D、E 分别在 AB、AC 上，DE∥BC，AD:DB=3:4，AE=6，求 EC。",
    "8. 在 Rt△ABC 中，∠C=90°，D 是 AB 上一点，DE⊥AC 于 E，DF⊥BC 于 F，已知 AC=5，BC=12，求矩形 DECF 面积的最大值。",
    "9. 在△ABC 中，∠A=90°，AD⊥BC 于 D，AB=6，AC=8，求 BD 和 CD。",
    "10. 已知△ABC∽△DEF，∠A=∠D，∠B=∠E，AB=4，DE=6，AC=5，求 DF。",
    "11. 在△ABC 中，D 是 AB 上一点，且 ∠ACD=∠B，AC=4，AB=6，求 AD。",
    "12. 在 Rt△ABC 中，∠ACB=90°，CD⊥AB 于 D，若 AD:BD=1:4，求 AC:BC。",
    "13. 在△ABC 中，D、E 分别在 AB、AC 上，DE∥BC，若 S△ADE:S△ABC=1:4，求 AD:AB。",
    "14. 在 Rt△ABC 中，∠C=90°，AB=10，AC=6，以 AB 为斜边作等腰直角三角形 ABD，求 CD。",
    "15. 在△ABC 中，D 是 BC 中点，E 是 AC 中点，AD 与 BE 交于 F，若 S△ABC=12，求 S△ABF。",
    "16. 在梯形 ABCD 中，AD∥BC，对角线 AC、BD 交于 O，若 AD=3，BC=6，求 AO:OC。",
    "17. 在 Rt△ABC 中，∠C=90°，AC=4，BC=3，点 D 在 AB 上，AD:DB=2:1，过 D 作 DE⊥AC 于 E，DF⊥BC 于 F，求矩形 DECF 的周长。",
    "18. 在△ABC 中，∠A=2∠B，CD 是∠C 的平分线，D 在 AB 上，AC=6，BC=9，求 AD:DB。",
    "19. 在 Rt△ABC 中，∠C=90°，CD⊥AB 于 D，DE⊥AC 于 E，已知 AD=2，BD=8，求 DE。",
    "20. 已知△ABC∽△ADE，AB=6，AD=4，AC=9，求 AE。"
]

for prob in geo_problems:
    p = doc.add_paragraph()
    run = p.add_run(prob)
    run.font.size = Pt(11)
    p.paragraph_format.space_after = Pt(4)

# 圆
doc.add_page_break()
h2 = doc.add_heading('', level=2)
run = h2.add_run('圆的切线、圆周角、圆幂定理（15道）')
run.font.color.rgb = RGBColor(0, 76, 153)

circle_problems = [
    "1. PA 是⊙O 的切线，A 为切点，PO 交⊙O 于 B，PA=6，OA=4，求 PB。",
    "2. AB 是⊙O 的直径，C 是⊙O 上一点，∠ABC=40°，求∠ACB 和∠BAC。",
    "3. PA、PB 是⊙O 的两条切线，A、B 为切点，∠APB=60°，PA=2，求 AB。",
    "4. AB 是⊙O 的直径，CD 是弦，CD⊥AB 于 E，CE=3，BE=1，求 AB。",
    "5. PA 是⊙O 的切线，A 为切点，PB 是割线，交⊙O 于 C、D，PA=4，PC=2，PD=8，求⊙O 的半径。",
    "6. AB 是⊙O 的直径，C 是⊙O 上一点，CD⊥AB 于 D，AD=2，BD=8，求 CD。",
    "7. PA、PB 是⊙O 的两条切线，A、B 为切点，∠APB=80°，求∠AOB。",
    "8. AB、AC 是⊙O 的两条弦，∠ABC=50°，∠ACB=70°，求∠BAC 和∠BOC。",
    "9. PA 是⊙O 的切线，A 为切点，PBC 是割线，PA=6，PC=12，求 PB。",
    "10. AB 是⊙O 的直径，弦 CD⊥AB 于 E，CE=4，AB=10，求 OE。",
    "11. PA、PB 是⊙O 的切线，A、B 为切点，AB 交 OP 于 C，PA=5，PC=3，求⊙O 的半径。",
    "12. AB 是⊙O 的直径，点 C 在⊙O 上，∠CAB=30°，BC=2，求 AB。",
    "13. PA 是⊙O 的切线，A 为切点，PO 交⊙O 于 C、D，PA=4，PC=2，求 PD。",
    "14. AB、CD 是⊙O 的两条弦，交于 P，PA·PB=PC·PD，若 PA=3，PB=4，PC=2，求 PD。",
    "15. 在⊙O 中，弦 AB=CD，AB 与 CD 相交于 P，PA=2，PB=6，若 PC:PD=1:3，求 PC、PD。"
]

for prob in circle_problems:
    p = doc.add_paragraph()
    run = p.add_run(prob)
    run.font.size = Pt(11)
    p.paragraph_format.space_after = Pt(4)

# 保存到桌面
desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
filepath = os.path.join(desktop, '数学练习题汇编.docx')
doc.save(filepath)
print(f'文档已保存到: {filepath}')
