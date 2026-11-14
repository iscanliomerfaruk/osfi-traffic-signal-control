# Factual Inconsistencies and Methodological Anomalies in Esmaeili et al. (2025)

A rigorous inspection of the reference paper — Esmaeili, Anjomshoae, Shahsavari-Pour, Srisurin, & Banomyong (2025), *"An optimization similarity fuzzy inference method for traffic signal control at an isolated intersection"*, Multimodal Transportation 4, 100234 — reveals several mathematical, numerical, and physical inconsistencies. Every item below has been verified directly against the published PDF.

---

## 1. Inverted Sign Convention and Denominator Switch in `Average Exit (veh)` Improvements (Abstract, Tables 1–3, Sec. 5.2–5.4)

- **Where in paper:** Abstract (p. 1), Table 1 (p. 13), Table 2 (p. 14), Fig. 9 (p. 15), Sec. 5.2–5.3 (p. 14–15), Table 3 (p. 16), Fig. 11 & Sec. 5.4 (p. 17).
- **The inconsistency:**
  1. **Metric definition vs. reported numbers:** Section 5.2 (p. 14–15) states: *"the average exit rate reflects the number of vehicles exiting the intersection per phase during the simulation period. These metrics are critical in assessing the efficiency of traffic signal controllers, as lower delays and **higher exit rates** indicate better traffic flow management."* Yet in **every phase** of Table 1 (p. 13) and Table 2 (p. 14), OSFI has **fewer** or equal exiting vehicles compared to Mamdani and Sugeno:
     - **Table 1 (Moderate), Phase E:** Mamdani $= 328$, Sugeno $= 320$, OSFI $= 310$ veh. Despite OSFI discharging **18 fewer vehicles** than Mamdani ($-5.49\%$) and **10 fewer** than Sugeno ($-3.13\%$), Table 1 reports this as `+5.49%` and `+3.13%` improvement!
     - **Table 1 (Moderate), Phase W:** Mamdani $= 165$, Sugeno $= 145$, OSFI $= 138$ veh ($-16.36\%$ vs. Mamdani, $-4.83\%$ vs. Sugeno), which Section 5.3 (p. 15) describes as: *"The West phase, for instance, saw a 16.36% improvement in vehicle exit rates when using OSFI compared to Mamdani and a 4.83% improvement compared to Sugeno. This is a critical metric because it shows that the OSFI method not only reduces delays but also enables a higher volume of vehicles to clear the intersection..."*
     - **Table 2 (Heavy), Phase W:** Mamdani $= 152$, Sugeno $= 137$, OSFI $= 128$ veh. Abstract (p. 1) and Sec. 5.3 (p. 15) claim *"traffic throughput improvements of up to 18.75% during heavy traffic"*, when in fact $128 < 152$ is a **$15.79\%$ reduction** in discharged vehicles (and $(152 - 128) / 128 = +18.75\%$).
  2. **Self-contradiction inside Section 5.4:** On p. 16–17, describing Fig. 9, the text claims *"Particularly in the West phase, where traffic congestion tends to peak, OSFI significantly increases the number of vehicle exits compared to both Sugeno (red bars) and Mamdani (orange bars)"* — even though the blue bar (OSFI) in Fig. 9 is visibly the **shortest** bar in Phase W! Two paragraphs later, describing Fig. 11 on p. 17, the text contradicts itself and admits: *"OSFI exhibits slightly lower vehicle throughput in the East and West phases."*
  3. **Inconsistent percentage formula between Table 1 and Table 2:**
     - In **Table 1** (p. 13), percentage differences are computed with the **baseline** in the denominator: $(\text{Baseline} - \text{OSFI}) / \text{Baseline}$ (e.g., Phase E Exit: $(328 - 310)/328 = 5.488\% \approx 5.49\%$; Phase W Exit: $(165 - 138)/165 = 16.364\% \approx 16.36\%$).
     - In **Table 2** (p. 14), the denominator is silently switched to **OSFI**: $(\text{Baseline} - \text{OSFI}) / \text{OSFI}$ (e.g., Phase N Delay: $(1.144 - 1.082)/1.082 = 5.730\%$; Phase E Exit: $(347 - 298)/298 = 16.443\%$; Phase W Exit: $(152 - 128)/128 = 18.750\%$; Phase N Exit: $(186 - 178)/178 = 4.494\%$).
  4. **Arithmetic errors in individual cells:**
     - In Table 1 (p. 13), Phase N `Average Exit` has Mamdani $= 173$ and OSFI $= 173$ (identical), but the Comparison column reports `0.58%` instead of `0.00%` ($1/173 = 0.578\%$, as if one of the numbers was $174$ or $172$).
     - In Table 2 (p. 14), Phase W `Average Exit` has Sugeno $= 137$ and OSFI $= 128$, which gives $(137 - 128)/137 = 6.57\%$ (or $(137 - 128)/128 = 7.03\%$), yet the table reports `2.34%` (which corresponds to $(131 - 128)/128 = 2.344\%$).

---

## 2. Contradictory Delay Reduction Ranges Between Text (Sec. 5.3) and Tables 1 & 3

- **Where in paper:** Section 5.3 (p. 15, paragraph 2) vs. Table 1 (p. 13) and Table 3 (p. 16).
- **The inconsistency:**
  - Section 5.3 (p. 15) states: *"As shown in Table 1, the average delay under the OSFI method was reduced by **3.55% to 3.78%** compared to the Mamdani method"* (taking only Phase E's `3.55%` and Phase N's `3.78%` while ignoring Phase S's `2.31%` and Phase W's `1.62%`).
  - Table 1 (p. 13) and Table 3 (p. 16) list the actual range across the four phases as **`1.62% to 3.78%`**.

---

## 3. Physically Implausible Average Vehicle Delays ($\approx 1.01–1.21\text{ s/veh}$) for a 4-Phase Signal

- **Where in paper:** Tables 1 and 2 (p. 13–14), Figs. 8 and 10 (p. 14, 16), Sec. 4 (p. 7–8).
- **The inconsistency:**
  - Section 4 (p. 7–8) specifies a four-legged intersection operating in **four sequential phases** where *"only one phase is granted green time at a given moment."*
  - Even under an idealized zero-lost-time cycle with minimal green durations of $7\text{ s}$ per phase (total cycle $C = 28\text{ s}$, red duration $R = 21\text{ s}$ per phase), the uniform arrival delay formula $d_1 = \frac{C(1 - g/C)^2}{2(1 - y)}$ yields a minimum baseline delay of **at least $7.9\text{ s/veh}$** at zero flow ($y \to 0$) and **$15–100+\text{ s/veh}$** under moderate-to-heavy demand with intergreen lost times.
  - Reporting average delays of **$1.011\text{ s}$ to $1.210\text{ s}$** across all four phases under moderate and heavy traffic is physically impossible for a 4-phase intersection unless the reported numbers represent a non-standard quantity (e.g., per-step queueing increment, single-server service time $1/\mu$ without red-phase waiting, or normalized units).

---

## 4. Contradiction Between Claimed Defuzzification Methods and Non-Operationalized OSFI Theory

- **Where in paper:** Section 3.1–3.2 (p. 6–7, Eq. 1), Section 4.1.2 (p. 10–11), Section 5 (p. 14), Section 5.1 (p. 14).
- **The inconsistency:**
  1. **Weighted average vs. Centroid:** Section 4.1.2 (p. 10–11) explicitly defines the inference mechanism of $\text{FC}_1$ and $\text{FC}_2$ as a zero-order Sugeno-style weighted average of crisp singleton outputs $z = c$:
     $$\alpha_i = \text{AND Operation}(f_1, f_2), \qquad \text{Output} = \frac{\sum_{i=1}^N \alpha_i Z_i}{\sum_{i=1}^N \alpha_i}.$$
     However, Section 5 (p. 14) and Section 5.1 (p. 14) state: *"The centroid defuzzification method was applied across all three controllers to maintain consistency during output processing."* A crisp singleton weighted average and continuous centroid defuzzification are distinct mechanisms (in particular, on Fig. 6's asymmetric Zero triangle $\text{Z}=(0,0,7.5)$, centroid defuzzification yields $\approx 2.5\text{ s}$ whereas the peak constant is $0\text{ s}$).
  2. **"Łukasiewicz implicator" used as an AND operator:** Section 4.1.2 (p. 10) states: *"The AND operation is implemented using the Łukasiewicz implicator, where the functions $f_1$ and $f_2$ represent the membership functions of the input variables."* Mathematically, a fuzzy implicator satisfies $I(0,0)=1$ and $I(0,1)=1$ (Definition 3, p. 6), which would assign firing strength $\alpha_i = 1$ to rules whose antecedent has **zero** membership! The authors either meant the **Łukasiewicz t-norm** $T_{\text{Lu}}(a,b) = \max(0, a+b-1)$ (conjunction) or misstated the role of the implicator. Moreover, when $T_{\text{Lu}}(f_1, f_2) = \max(0, f_1+f_2-1)$ is used with the Gaussian MFs of Figs. 4–5, inputs midway between two centers (e.g., $\lambda = 1.5, q = 7.5\text{ m}$, where $\max \mu_\lambda = \max \mu_q = e^{-1.125} \approx 0.325$) satisfy $f_1 + f_2 \approx 0.65 \le 1$, causing $\sum_{i=1}^N \alpha_i = 0$ and a division by zero ($0/0$) in the weighted average formula on p. 11.
  3. **Disconnect between Section 3.2 (Eq. 1) and Section 4.1.2:** Section 3.2 (p. 7) formulates OSFI as the Deng & Jiang (2014) truth-table similarity maximization problem $\max \Phi(E_B^*) = \text{Sim}(E_A \to E_B, E_A^* \to E_B^*)$, but Section 4.1.2 never specifies which similarity measure $\text{Sim}$, implicator $\to$, or discrete universe is used to solve Eq. (1), instead switching to the weighted-average formula on p. 11.

---

## 5. Mathematical Errors in Preliminaries (Definitions 3 & 4, Sec. 3.1, p. 6–7)

- **Where in paper:** Definition 3 (p. 6) and Definition 4 (p. 7).
- **The inconsistency:**
  1. **Mamdani $\min(a,b)$ listed as satisfying Definition 3:** Definition 3 (p. 6) defines a fuzzy implicator on $[0,1]$ as a mapping satisfying the boundary conditions $I(0,0)=1$, $I(1,0)=0$, $I(0,1)=1$, and $I(1,1)=1$. Immediately below, Example 1 lists *"1) Mamdani implicator $I_{\text{Min}}(a,b) = \min(a,b)$"*, which gives $I_{\text{Min}}(0,0) = 0 \neq 1$ and $I_{\text{Min}}(0,1) = 0 \neq 1$, violating two of the four axioms just stated.
  2. **Notation typo in Example 3:** Example 3 on p. 6 (Goguen implicator) is denoted $I_{Lu}(a,b)$ (reusing the Łukasiewicz subscript from Example 2).
  3. **Misattributed citation in Definition 4:** Definition 4 (p. 7) attributes the four standard axioms of a fuzzy similarity measure $S_e : FS(E) \times FS(E) \to [0,1]$ to `(Webster, 1958; Sun et al., 2024)` — two traffic signal timing papers that do not define fuzzy set similarity axioms (Webster 1958 predates Zadeh's 1965 fuzzy set paper by seven years).

---

## 6. Discrepancies Between Membership Function Text Intervals and Figures 4–7 (Sec. 4.1.2, p. 11–13)

- **Where in paper:** Bullet lists on p. 12 vs. Fig. 4 (p. 11), Fig. 5 (p. 11), Fig. 6 (p. 12), and Fig. 7 (p. 13).
- **The inconsistency:**
  - **Extension1 (`Fig. 6` vs. p. 12 text):** The text on p. 12 states that `Extension1` is classified as $\text{Z} \in [0, 7]$, $\text{Sh} \in [0, 13]$, $\text{M} \in [7, 17]$, and $\text{L} \in [13, 25]$ s. However, Fig. 6 clearly plots triangular membership functions with vertices at half-integer multiples of $2.5$: $\text{Z}=(0, 0, 7.5)$, $\text{Sh}=(0, 7.5, 12.5)$, $\text{M}=(7.5, 12.5, 17.5)$, and $\text{L}=(12.5, 17.5, 22.5)$ (reaching $0$ at $22.5\text{ s}$, not $25\text{ s}$).
  - **Arrival rate (`Fig. 4`) and Queue length (`Figs. 5, 7`):** The text on p. 12 describes crisp support intervals ($\lambda$: $[0,3], [0,6], [3,9], [6,12]$; $q$: $[0,15], [0,30], [15,45], [30,60]$), whereas Figs. 4, 5, and 7 plot smooth Gaussian functions ($\sigma_\lambda = 1.0$, $\sigma_q = 5.0$) that are strictly positive across the entire universe.

---

## 7. Incomplete Rule Bases and Unspecified Experimental Protocol (Sec. 4.1.2 & Sec. 5.1)

- **Where in paper:** Section 4.1.2 (p. 12–13) and Section 5.1 (p. 14).
- **The inconsistency:**
  - **Missing rules:** Section 4.1.2 states that $\text{FC}_1$ uses 16 rules and $\text{FC}_2$ uses 13 rules, but only prints 3 rules of $\text{FC}_1$ (p. 12) and 3 rules of $\text{FC}_2$ (p. 13), leaving 23 of the 29 rules unstated.
  - **Unspecified simulation setup and data:** Section 5.1 (p. 14) states *"The simulation was executed using a combination of synthetic data and real-world traffic data, ensuring robust results that reflect practical scenarios"*, but never identifies any real-world intersection, city, dataset, arrival rates (veh/h), saturation flow rates, lane configurations, signal lost times, simulation duration, number of random seeds/replications, or variance/confidence intervals.
