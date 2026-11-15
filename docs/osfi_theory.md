# Mathematical Theory of Optimization Similarity Fuzzy Inference (OSFI) and Singleton Equivalence

This document presents the complete mathematical formulation of the **Optimization Similarity Fuzzy Inference (OSFI)** method introduced by Deng & Jiang (2014) and cited in Section 3.2 (Eq. 1) of Esmaeili et al. (2025). We then state and prove the **Singleton Equivalence Proposition**, which establishes that under singleton fuzzification, OSFI and Zadeh's Compositional Rule of Inference (CRI) produce identical fuzzy conclusions for both true implicators (Łukasiewicz, Goguen, Kleene-Dienes) and the Mamdani minimum operator, and that the truth-table similarity optimization alters the inference outcome **if and only if** the observed input is a non-singleton fuzzy set.

---

## 1. Truth-Table Similarity Optimization (Deng & Jiang, 2014)

Consider a fuzzy modus ponens rule over discrete finite universes $X = \{x_1, \dots, x_m\}$ (where each $x \in X$ may be a two-dimensional input tuple $x = (x_1, x_2) \in X_1 \times X_2$) and $Y = \{y_1, \dots, y_n\}$:

$$
\begin{aligned}
\text{Rule:} \quad & A(x) \to B(y) \\
\text{Fact:} \quad & A^*(x) \\
\hline
\text{Conclusion:} \quad & B^*(y)
\end{aligned}
$$

Here $A, A^* \in \mathcal{F}(X)$ are fuzzy sets on $X$, $B, B^* \in \mathcal{F}(Y)$ are fuzzy sets on $Y$, and $I : [0, 1] \times [0, 1] \to [0, 1]$ is a fuzzy implicator (or conjunction operator in the Mamdani case).

For the two-input rules in $\text{FC}_1$ and $\text{FC}_2$, the rule antecedent membership is constructed via the Łukasiewicz t-norm $T_{\text{Lu}}(u, v) = \max(0, u + v - 1)$:

$$
A_i(x_1, x_2) = T_{\text{Lu}}\!\left(A_{i,1}(x_1),\, A_{i,2}(x_2)\right).
$$

Given the rule $A \to B$ and a candidate conclusion $B^* \in \mathcal{F}(Y)$ for the observed input $A^* \in \mathcal{F}(X)$, two fuzzy relations ("truth tables") on $X \times Y$ are formed:

$$
R(x, y) = I\!\left(A(x),\, B(y)\right), \qquad R^*(x, y) = I\!\left(A^*(x),\, B^*(y)\right).
$$

Deng & Jiang (2014) formulate fuzzy reasoning as finding the fuzzy set $B^* \in \mathcal{F}(Y)$ that maximizes the similarity between the rule truth table $R$ and the induced truth table $R^*$:

$$
B^* = \arg\max_{B^* \in \mathcal{F}(Y)} \operatorname{Sim}\!\left(R,\, R^*\right),
$$

using the normalized $\ell_1$ ($d_1$) similarity measure on $\mathcal{F}(X \times Y)$:

$$
\operatorname{Sim}_{d_1}\!\left(R,\, R^*\right) = 1 - \frac{1}{|X|\,|Y|} \sum_{y \in Y} \sum_{x \in X} \left| R(x, y) - R^*(x, y) \right|.
$$

### 1.1. Pointwise Separability over $Y$

Because $R^*(x, y) = I(A^*(x), B^*(y))$ depends on $B^*$ at coordinate $y$ solely through the scalar value $b = B^*(y) \in [0, 1]$, the double sum decouples completely across $y \in Y$. Maximizing $\operatorname{Sim}_{d_1}(R, R^*)$ over $B^* \in \mathcal{F}(Y)$ is therefore equivalent to solving, independently for each $y \in Y$, the one-dimensional minimization problem:

$$
B^*(y) = \arg\min_{b \in [0, 1]} J_y(b), \qquad J_y(b) \triangleq \sum_{x \in X} \left| I\!\left(A(x),\, B(y)\right) - I\!\left(A^*(x),\, b\right) \right|.
$$

When the minimizer of $J_y(b)$ on $[0, 1]$ is an interval $[b_{\min}(y), b_{\max}(y)]$ (non-uniqueness, analyzed by Deng & Jiang, 2014), selecting the smallest minimizer $b_{\min}(y)$ yields the most specific (least uncertain) fuzzy conclusion under the specificity ordering of implication-based inference; alternative tie-breaking rules select the largest minimizer $b_{\max}(y)$ or the interval midpoint $\frac{1}{2}(b_{\min}(y) + b_{\max}(y))$.

---

## 2. Proposition: Singleton Equivalence of OSFI-DJ and CRI

### Proposition 1 (Coincidence of OSFI-DJ and CRI under Singleton Fuzzification)

Let $x_0 \in X$ be an arbitrary grid point, and let the observed input $A^* \in \mathcal{F}(X)$ be the singleton fuzzy set concentrated at $x_0$:

$$
A^*(x) = \begin{cases}
1, & \text{if } x = x_0, \\
0, & \text{if } x \neq x_0.
\end{cases}
$$

1. **True Implicators (Łukasiewicz, Goguen, Kleene-Dienes):** Suppose the implicator $I : [0, 1]^2 \to [0, 1]$ satisfies the left-boundary and neutrality properties:
   $$
   I(0, b) = 1 \quad \text{and} \quad I(1, b) = b, \qquad \forall b \in [0, 1].
   $$
   Then for every $y \in Y$, the OSFI-DJ objective $J_y(b)$ has the **unique** minimizer on $[0, 1]$:
   $$
   B^*_{\text{OSFI}}(y) = I\!\left(A(x_0),\, B(y)\right),
   $$
   which coincides identically with the sup-$T$ Compositional Rule of Inference (CRI) output $B^*_{\text{CRI}}(y) = \sup_{x \in X} T(A^*(x), I(A(x), B(y)))$ for any t-norm $T$.

2. **Mamdani Minimum Operator ($I_{\min}(a, b) = \min(a, b)$):** Although $I_{\min}$ is not a true implicator because $I_{\min}(0, b) = 0 \neq 1$, it satisfies:
   $$
   I_{\min}(0, b) = 0 \quad \text{and} \quad I_{\min}(1, b) = b, \qquad \forall b \in [0, 1].
   $$
   Under singleton fuzzification at $x_0$, the OSFI-DJ objective $J_y(b)$ has the **unique** minimizer on $[0, 1]$:
   $$
   B^*_{\text{OSFI},\min}(y) = \min\!\left(A(x_0),\, B(y)\right),
   $$
   which is exact Mamdani clipping and coincides identically with Mamdani CRI.

---

### Proof

#### Part 1: True Implicators ($I(0, b) = 1$, $I(1, b) = b$)

First, verify that the three standard implicators satisfy the hypotheses for all $b \in [0, 1]$:
- **Łukasiewicz:** $I_{\text{Lu}}(a, b) = \min(1, 1 - a + b) \implies I_{\text{Lu}}(0, b) = \min(1, 1 + b) = 1$ and $I_{\text{Lu}}(1, b) = \min(1, b) = b$.
- **Goguen:** $I_{\text{G}}(a, b) = 1$ if $a \le b$ else $b / a \implies I_{\text{G}}(0, b) = 1$ (since $0 \le b$) and $I_{\text{G}}(1, b) = b / 1 = b$.
- **Kleene-Dienes:** $I_{\text{KD}}(a, b) = \max(1 - a, b) \implies I_{\text{KD}}(0, b) = \max(1, b) = 1$ and $I_{\text{KD}}(1, b) = \max(0, b) = b$.

Now split the OSFI-DJ objective sum $J_y(b)$ into the $x = x_0$ term and the $x \neq x_0$ terms:

$$
J_y(b) = \left| I\!\left(A(x_0),\, B(y)\right) - I\!\left(A^*(x_0),\, b\right) \right| + \sum_{x \in X \setminus \{x_0\}} \left| I\!\left(A(x),\, B(y)\right) - I\!\left(A^*(x),\, b\right) \right|.
$$

Since $A^*(x_0) = 1$ and $A^*(x) = 0$ for all $x \neq x_0$, applying $I(1, b) = b$ and $I(0, b) = 1$ yields:

$$
J_y(b) = \left| I\!\left(A(x_0),\, B(y)\right) - b \right| + \underbrace{\sum_{x \in X \setminus \{x_0\}} \left| I\!\left(A(x),\, B(y)\right) - 1 \right|}_{C_1(y),\text{ independent of } b}.
$$

Because $C_1(y)$ does not depend on $b$, $J_y(b) - C_1(y) = |I(A(x_0), B(y)) - b| \ge 0$, with equality if and only if:

$$
b = I\!\left(A(x_0),\, B(y)\right) \in [0, 1].
$$

Hence $B^*_{\text{OSFI}}(y) = I(A(x_0), B(y))$ is the unique global minimizer.

Meanwhile, for CRI with any t-norm $T$ (which satisfies the t-norm boundary axioms $T(0, r) = 0$ and $T(1, r) = r$ for all $r \in [0, 1]$):

$$
B^*_{\text{CRI}}(y) = \sup_{x \in X} T\!\left(A^*(x),\, I(A(x), B(y))\right) = \max\!\left\{ T\!\left(1,\, I(A(x_0), B(y))\right),\, \max_{x \neq x_0} T\!\left(0,\, I(A(x), B(y))\right) \right\} = I\!\left(A(x_0),\, B(y)\right).
$$

Thus $B^*_{\text{OSFI}}(y) = B^*_{\text{CRI}}(y)$ for all $y \in Y$.

#### Part 2: Mamdani Minimum Operator ($I_{\min}(a, b) = \min(a, b)$)

For $I_{\min}(a, b) = \min(a, b)$, we have $I_{\min}(0, b) = \min(0, b) = 0$ and $I_{\min}(1, b) = \min(1, b) = b$ for all $b \in [0, 1]$. Substituting the singleton $A^*$ into $J_y(b)$ gives:

$$
J_y(b) = \left| \min\!\left(A(x_0),\, B(y)\right) - b \right| + \underbrace{\sum_{x \in X \setminus \{x_0\}} \left| \min\!\left(A(x),\, B(y)\right) - 0 \right|}_{C_0(y),\text{ independent of } b}.
$$

Again, $C_0(y)$ is constant in $b$, and $| \min(A(x_0), B(y)) - b |$ is uniquely minimized at $b = \min(A(x_0), B(y))$, which is identical to Mamdani CRI clipping. $\blacksquare$

---

## 3. Corollary: Support Restriction ($A^*(x) > 10^{-3}$) and Non-Singleton Divergence

1. **Invariance under zero/near-zero support pruning:**
   For any grid cell $x \in X$ where $A^*(x) = 0$, the term $|I(A(x), B(y)) - I(0, b)|$ is strictly independent of $b \in [0, 1]$ (since $I(0, b) \equiv 1$ for true implicators and $I_{\min}(0, b) \equiv 0$ for Mamdani). Consequently, removing all cells with $A^*(x) = 0$ changes $J_y(b)$ only by an additive constant $C_{\text{inactive}}(y)$ and leaves $\arg\min_{b \in [0, 1]} J_y(b)$ **unchanged**. Restricting the sum to $\{x \in X : A^*(x) > 10^{-3}\}$ eliminates $>95\%$ of grid cells in non-singleton mode with negligible perturbation.

2. **Why OSFI-DJ and CRI diverge under Non-Singleton Inputs:**
   Suppose the sensor measurement $(\hat{x}_1, \hat{x}_2)$ is corrupted by uncertainty $(\sigma_1, \sigma_2)$ and modeled as a non-singleton Gaussian fuzzy set $A^*(x_1, x_2) = \exp\!\left(-\frac{(x_1 - \hat{x}_1)^2}{2\sigma_1^2}\right)\exp\!\left(-\frac{(x_2 - \hat{x}_2)^2}{2\sigma_2^2}\right)$. Now multiple grid points $x \in X$ satisfy $0 < A^*(x) \le 1$:
   - **CRI ($\sup$-$T$ composition)** computes the worst-case envelope:
     $$B^*_{\text{CRI}}(y) = \max_{x \in X} T\!\left(A^*(x),\, R(x, y)\right),$$
     which is dominated by the single grid cell $x$ that maximizes $T(A^*(x), R(x, y))$ (an $\ell_\infty$-type extremum sensitive to outlier firing strengths across the uncertainty neighborhood).
   - **OSFI-DJ ($d_1$ similarity optimization)** solves:
     $$B^*_{\text{OSFI}}(y) = \arg\min_{b \in [0, 1]} \sum_{x \in X : A^*(x) > 10^{-3}} \left| R(x, y) - I\!\left(A^*(x),\, b\right) \right|,$$
     which is an $\ell_1$ (median-like) consensus estimator across the entire active neighborhood of $A^*$. This provides natural smoothing against sensor measurement noise.
