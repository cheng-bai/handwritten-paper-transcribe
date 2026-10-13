#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向明卷硬题：Q11 / Q16 / Q20(3) / Q21(3) 数值验证（向量化，轻量）。"""
import math
import numpy as np

print("=" * 68)
print("Q11  三矩形 50x10，AB=BC=10，∠BFC=∠HID 求 CD")
print("=" * 68)
L, W, BC = 50.0, 10.0, 10.0
sint = BC / L
cost = math.sqrt(1 - sint * sint)
u = np.array([sint, -cost]); n = np.array([cost, sint])
F = np.array([10.0, L * cost]); C = np.array([20.0, 0.0])
G = F + W * n; H = C + W * n
s2, c2 = math.sin(2 * math.asin(sint)), math.cos(2 * math.asin(sint))
v = np.array([s2, -c2])
t = (G[1] - L * c2) / cost
I = G + t * u; D = I + L * v
def ang(p, q, r):
    A = math.atan2(q[1]-p[1], q[0]-p[0]); B = math.atan2(r[1]-p[1], r[0]-p[0])
    d = abs(A-B); return math.degrees(min(d, 2*math.pi-d))
print(f"  sinθ={sint}  cosθ={cost:.6f}  tanθ={sint/cost:.6f}")
print(f"  F={np.round(F,4)} G={np.round(G,4)} H={np.round(H,4)}")
print(f"  I={np.round(I,4)} D={np.round(D,4)}")
print(f"  ∠BFC={ang(F,np.array([10,0]),C):.4f}°  ∠HID={ang(I,H,D):.4f}°")
print(f"  CD={D[0]-C[0]:.6f}   25√6/3={25*math.sqrt(6)/3:.6f}")

print()
print("=" * 68)
print("Q16  max b·(c-a), a=(2,0), b,c 在 圆(1,0)r=1")
print("=" * 68)
al = np.linspace(0, 2*np.pi, 3001)[:-1]
bx = 1 + np.cos(al)[:, None]; by = np.sin(al)[:, None]
cx = 1 + np.cos(al)[None, :]; cy = np.sin(al)[None, :]
print(f"  数值 max = {(bx*(cx-2) + by*cy).max():.8f}   (理论 1/2)")

print()
print("=" * 68)
print("Q20(3)  Γ: x²/4+y²=1(y≥0)，T(t,0) 直角顶点等腰直角三角形存在性")
print("=" * 68)
al = np.linspace(0, np.pi, 400001)
A = 5.0
sn, c2a = np.sin(al), 2*np.cos(al)
Bc = -2*(sn + 4*c2a)
Cc = sn*sn + 16*np.cos(al)**2 - 4
disc = Bc*Bc - 4*A*Cc
ok = disc >= 0
t1 = (-Bc[ok] + np.sqrt(disc[ok]))/(2*A); t2 = (-Bc[ok] - np.sqrt(disc[ok]))/(2*A)
need = 2*np.cos(al)[ok]
S = np.concatenate([t1[t1 <= need+1e-9], t2[t2 <= need+1e-9]])
full = np.concatenate([S, -S])
print(f"  旋转+90° 的 t 集: [{S.min():.5f}, {S.max():.5f}]")
print(f"  含两种旋转(取并): [{full.min():.5f}, {full.max():.5f}]")
for nm, val in [("-√3",-math.sqrt(3)),("-1",-1.0),("0",0.0),("1",1.0),("√3",math.sqrt(3)),("2",2.0)]:
    print(f"     {nm:>5}={val:+.5f}  in[{full.min():.3f},{full.max():.3f}]? {full.min()-0.02<=val<=full.max()+0.02}")

print()
print("=" * 68)
print("Q21(3)  f=x⁴-4x², g=4x²-16, [m,n]⊆[-2,2]，直线夹中间, max(n-m)")
print("=" * 68)
xs = np.linspace(-2, 2, 1201)
Fv = xs**4 - 4*xs**2
Gv = 4*xs**2 - 16
best = (0.0, None)
for k in np.arange(-8, 8.0001, 0.1):
    h = Fv - k*xs
    p = Gv - k*xs
    lo, hi = p.min(), h.max()
    for b in np.linspace(lo, hi, 500):
        mask = (p <= b) & (h >= b)
        idx = np.flatnonzero(mask)
        if idx.size == 0:
            continue
        d = np.diff(idx); brk = np.flatnonzero(d > 1)
        starts = np.concatenate([[idx[0]], idx[brk+1]]); ends = np.concatenate([idx[brk], [idx[-1]]])
        lens = xs[ends] - xs[starts]
        j = lens.argmax()
        if lens[j] > best[0]:
            best = (lens[j], (k, b, xs[starts[j]], xs[ends[j]]))
print(f"  max(n-m) ≈ {best[0]:.5f}  k={best[1][0]:.2f} b={best[1][1]:.3f}  [m,n]=[{best[1][2]:.4f},{best[1][3]:.4f}]")
print(f"  参考 2√3={2*math.sqrt(3):.5f} 2√2={2*math.sqrt(2):.5f} 3.5 √12={math.sqrt(12):.5f}")
