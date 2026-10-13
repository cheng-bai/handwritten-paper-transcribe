#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向明中学10月卷 硬题数值验证 / 求解。
覆盖：Q11（画框三矩形）、Q16（向量最值）、Q20(3)（等腰直角存在性 t 范围）、Q21(3)（n-m 最大值）。
"""
import math

print("=" * 70)
print("Q11  三个 50x10 矩形：AB=BC=10，∠BFC=∠HID，求 CD")
print("=" * 70)
BC = 10.0
L, W = 50.0, 10.0
# rect1 竖直：A(0,0) B(10,0) E(10,50)；rect2 左上角 F 落在 BE(x=10) 上，左下角 C(20,0)
f_y = math.sqrt(L * L - BC * BC)          # F=(10, f_y)
sint = BC / L                              # sinθ = 10/50 = 1/5
cost = math.sqrt(1 - sint * sint)          # 2√6/5
print(f"  FC=L=50 水平投影=BC=10 -> F=(10,{f_y:.4f})=20√6={20*math.sqrt(6):.4f}")
print(f"  sinθ={sint:.4f}  cosθ={cost:.6f}=2√6/5={2*math.sqrt(6)/5:.6f}  "
      f"tanθ={sint/cost:.6f}=1/(2√6)={1/(2*math.sqrt(6)):.6f}  θ={math.degrees(math.asin(sint)):.4f}°")
u = (sint, -cost)                # rect2 长轴方向（向下）
n = (cost, sint)                 # rect2 宽方向（右上）
F = (10.0, f_y)
G = (F[0] + W * n[0], F[1] + W * n[1])     # rect2 右上
C = (20.0, 0.0)
H = (C[0] + W * n[0], C[1] + W * n[1])     # rect2 右下
print(f"  G=({G[0]:.4f},{G[1]:.4f})   H=({H[0]:.4f},{H[1]:.4f})")
# rect3 左上角 I 在 GH 上；长轴倾角 2θ（使 ∠HID=θ）
s2, c2 = math.sin(2 * math.asin(sint)), math.cos(2 * math.asin(sint))
v = (s2, -c2)
t = (H[1] * 0 + G[1]) / cost if False else None
# D_y = G_y + t*(-cosθ) + 50*(-cos2θ) = 0
t = (G[1] - L * c2) / cost
I = (G[0] + t * u[0], G[1] + t * u[1])
D = (I[0] + L * v[0], I[1] + L * v[1])
print(f"  t={t:.4f}  I=({I[0]:.4f},{I[1]:.4f})  D=({D[0]:.4f},{D[1]:.4f})")
print(f"  CD = {D[0]-C[0]:.4f}   25√6/3 = {25*math.sqrt(6)/3:.4f}")
# 校验 ∠BFC 与 ∠HID
def ang(p, q, r):
    a1 = math.atan2(q[1]-p[1], q[0]-p[0]); a2 = math.atan2(r[1]-p[1], r[0]-p[0])
    d = abs(a1-a2); return math.degrees(min(d, 2*math.pi-d))
print(f"  ∠BFC={ang(F,(10,0),C):.4f}°  ∠HID={ang(I,H,D):.4f}°  (应相等)")

print()
print("=" * 70)
print("Q16  |a|=2, b,c 满足 a·b=|b|², a·c=|c|²，求 b·(c-a) 最大值")
print("=" * 70)
best = (-9e9, None)
N = 4000
for i in range(N):
    al = math.pi * 2 * i / N
    for j in range(N):
        be = math.pi * 2 * j / N
        b = (1 + math.cos(al), math.sin(al))
        c = (1 + math.cos(be), math.sin(be))
        val = b[0]*(c[0]-2) + b[1]*c[1]
        if val > best[0]:
            best = (val, (al, be))
print(f"  数值最大 b·(c-a) = {best[0]:.6f}   (理论 1/2 = 0.5)")

print()
print("=" * 70)
print("Q20(3)  Γ: x²/4+y²=1 (y≥0)，T(t,0)，以T为直角顶点的等腰直角三角形 存在性")
print("=" * 70)
ts = []
for i in range(0, 200001):
    t = -3.0 + 6.0 * i / 200000
    found = False
    for k in range(0, 3601):
        al = math.pi * k / 3600
        x, y = 2*math.cos(al), math.sin(al)
        qx, qy = t - y, x - t
        if qy < -1e-9:
            continue
        if abs(qx*qx/4 + qy*qy - 1) < 2e-3 and (abs(qx-x) > 1e-6 or abs(qy-y) > 1e-6):
            found = True; break
    if found:
        ts.append(t)
if ts:
    print(f"  存在 t 的数值区间: [{min(ts):.4f}, {max(ts):.4f}]  长度≈{max(ts)-min(ts):.4f}")
    for name, val in [("-√3", -math.sqrt(3)), ("-1", -1.0), ("0", 0.0), ("1", 1.0), ("√3", math.sqrt(3)), ("1+√2", 1+math.sqrt(2))]:
        pass
else:
    print("  未找到")

print()
print("=" * 70)
print("Q21(3)  f=x⁴-4x², g=4x²-16, [m,n]⊆[-2,2]，有直线夹在中间，求 max(n-m)")
print("=" * 70)
f = lambda x: x**4 - 4*x*x
g = lambda x: 4*x*x - 16
def feasible(m, n, K=400):
    xs = [m + (n-m)*k/K for k in range(K+1)]
    lo = max(g(x) for x in xs)     # 直线需 >= g  => 直线在 (x, g(x)) 之上
    hi = min(f(x) for x in xs)     # 直线需 <= f
    # 存在直线 ℓ 使 g<=ℓ<=f 于 [m,n]：等价于存在 k,b. 用线性规划：切比雪夫
    # 条件：∀x, g(x)<=kx+b<=f(x). 对全部 x 要一致（连续）
    # 用密集采样 + 线性规划可行性（LP 二维：变量 k,b）
    import itertools
    # 单纯用采样约束：g(x)-kx-b <=0 且 kx+b-f(x)<=0
    # 二维 LP 直接用 scipy 不可用，改为：枚举边界法
    # 可行等价于 max_x [g(x)-f(x)] <=0 且存在 k,b...
    # 简化：直接对 k,b 网格 + 精修
    return lo, hi, xs
# 用二维 LP：约束 a_i·(k,b) <= rhs_i ; a=g: (-x,-1) <= -g(x)?? 推
# g(x) <= kx+b  => -k x - b <= -g(x)  => (-x,-1)·(k,b) <= -g(x)
# kx+b <= f(x)  => (x,1)·(k,b) <= f(x)
try:
    from scipy.optimize import linprog
    HAVE = True
except Exception:
    HAVE = False
print("  scipy:", HAVE)
if HAVE:
    def feasible_lp(m, n, K=300):
        xs = [m + (n-m)*k/K for k in range(K+1)]
        A, b_ = [], []
        for x in xs:
            A.append([-x, -1]); b_.append(-g(x))
            A.append([x, 1]);   b_.append(f(x))
        r = linprog([0, 0], A_ub=A, b_ub=b_, bounds=[(None, None), (None, None)], method="highs")
        return r.status == 0
    bestlen, bestint = 0, None
    for i in range(0, 801):
        m = -2.0 + 4.0 * i / 800
        # 找最大 n
        lo, hi = m, 2.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if feasible_lp(m, mid):
                lo = mid
            else:
                hi = mid
        if lo - m > bestlen:
            bestlen, bestint = lo - m, (m, lo)
    print(f"  数值 max(n-m) ≈ {bestlen:.6f}  在 [m,n]≈[{bestint[0]:.4f},{bestint[1]:.4f}]")
    print(f"  参考: 2√3={2*math.sqrt(3):.6f}  4={4.0}  2√2={2*math.sqrt(2):.6f}  √10={math.sqrt(10):.6f}")
