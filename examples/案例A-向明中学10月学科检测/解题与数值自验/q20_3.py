#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q20(3) 精确求 t 集合：逐 α 解二次方程，剔除退化解，输出集合结构。"""
import math
import numpy as np

A = 5.0
al = np.linspace(1e-6, math.pi-1e-6, 2000001)   # 排除退化 α=0,π
sn = np.sin(al); cs = np.cos(al)
Bc = -2*(sn + 8*cs)
Cc = sn*sn + 16*cs*cs - 4
disc = Bc*Bc - 4*A*Cc
ok = disc >= 0
t1 = (-Bc[ok] + np.sqrt(disc[ok]))/(2*A)
t2 = (-Bc[ok] - np.sqrt(disc[ok]))/(2*A)
need = 2*cs[ok]                                  # Q_y = 2cosα - t >= 0
S = np.concatenate([t1[t1 <= need+1e-12], t2[t2 <= need+1e-12]])
S = S[np.isfinite(S)]
print("旋转 +90°：t 集")
print(f"  n={S.size}  min={S.min():.6f}  max={S.max():.6f}")
# 结构：分箱
hist, edges = np.histogram(S, bins=40, range=(-2.1, 2.1))
for cnt, e0, e1 in zip(hist, edges[:-1], edges[1:]):
    print(f"   [{e0:+.2f},{e1:+.2f}) {'#'*int(60*cnt/hist.max())} {cnt}")
# 旋转 -90°（等价于把 x->-x）：集合取并
full = np.concatenate([S, -S])
print(f"两种旋转并集: [{full.min():.6f}, {full.max():.6f}]")

# 直接逐 t 复核（更稳）：对每个 t 细扫 α
print()
print("逐 t 复核（细扫 α，要求 |残差|<1e-6 且 Q_y>=0, α∈(0,π)）:")
ts = np.linspace(-2.05, 2.05, 411)
found = []
for t in ts:
    res = (t - sn)**2/4 + (2*cs - t)**2 - 1
    good = (np.abs(res) < 2e-5) & (2*cs - t >= -1e-9)
    if good.any():
        found.append(t)
found = np.array(found)
if found.size:
    # 找最长连续段
    d = np.diff(found); brk = np.flatnonzero(d > 0.02)
    starts = np.concatenate([[0], brk+1]); ends = np.concatenate([brk, [len(found)-1]])
    print("  连续存在域:")
    for s, e in zip(starts, ends):
        print(f"    [{found[s]:+.4f}, {found[e]:+.4f}]")
