# Fuzzy Rule Bases (`FC1` and `FC2`)

The reference paper (Esmaeili et al., 2025, Sec. 4.1.2, pp. 12-13) specifies that:
- `FC1` contains **16 rules** mapping `(Arrival rate, Queue length) -> Extension1`, but lists only 3 example rules.
- `FC2` contains **13 rules** mapping `(Extension1, Queue length of other phases) -> Extension2`, and lists 3 example rules.

## 1. `FC1` Rule Base (16 Rules)

Design rule: with `Arrival rate` $a \in \{\text{Z}:0, \text{Lo}:1, \text{M}:2, \text{H}:3\}$ and `Queue length` $q \in \{\text{Sh}:0, \text{M}:1, \text{L}:2, \text{VL}:3\}$,
$$\text{Extension1} = \lfloor (a + q) / 2 \rfloor \in \{\text{Z}:0, \text{Sh}:1, \text{M}:2, \text{L}:3\}.$$

| Rule # | Arrival Rate ($\lambda$) | Queue Length ($q$) | Consequent (`Extension1`) | Verbatim in Paper? | Paper Reference |
| :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | `Z` | `Sh` | `Z` | Yes | FC1 Rule 1 (p. 12) |
| 2 | `Z` | `M` | `Z` | No (completed) | - |
| 3 | `Z` | `L` | `Sh` | No (completed) | - |
| 4 | `Z` | `VL` | `Sh` | No (completed) | - |
| 5 | `Lo` | `Sh` | `Z` | No (completed) | - |
| 6 | `Lo` | `M` | `Sh` | No (completed) | - |
| 7 | `Lo` | `L` | `Sh` | Yes | FC1 Rule 2 (p. 12) |
| 8 | `Lo` | `VL` | `M` | No (completed) | - |
| 9 | `M` | `Sh` | `Sh` | Yes | FC1 Rule 3 (p. 12) |
| 10 | `M` | `M` | `Sh` | No (completed) | - |
| 11 | `M` | `L` | `M` | No (completed) | - |
| 12 | `M` | `VL` | `M` | No (completed) | - |
| 13 | `H` | `Sh` | `Sh` | No (completed) | - |
| 14 | `H` | `M` | `M` | No (completed) | - |
| 15 | `H` | `L` | `M` | No (completed) | - |
| 16 | `H` | `VL` | `L` | No (completed) | - |

## 2. `FC2` Rule Base (13 Rules)

Design rule: with `Extension1` $e \in \{\text{Z}:0, \text{Sh}:1, \text{M}:2, \text{L}:3\}$ and competing queue penalty $\text{penalty}(q') \in \{\text{Sh}:0, \text{M}:0, \text{L}:1, \text{VL}:2\}$,
$$\text{Extension2} = \max(0, e - \text{penalty}(q')).$$
All four $e = \text{Z}$ combinations yield `Extension2 = Z` and collapse into a single rule (Rule 1), yielding $1 + 3 \times 4 = 13$ rules.

| Rule # | `Extension1` ($e$) | Other Phases Queue ($q'$) | Consequent (`Extension2`) | Verbatim in Paper? | Paper Reference |
| :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | `Z` | `ANY` (`Sh`, `M`, `L`, `VL`) | `Z` | Yes | FC2 Rule 1 (p. 13) |
| 2 | `Sh` | `Sh` | `Sh` | No (completed) | - |
| 3 | `Sh` | `M` | `Sh` | Yes | FC2 Rule 2 (p. 13) |
| 4 | `Sh` | `L` | `Z` | No (completed) | - |
| 5 | `Sh` | `VL` | `Z` | No (completed) | - |
| 6 | `M` | `Sh` | `M` | Yes | FC2 Rule 3 (p. 13) |
| 7 | `M` | `M` | `M` | No (completed) | - |
| 8 | `M` | `L` | `Sh` | No (completed) | - |
| 9 | `M` | `VL` | `Z` | No (completed) | - |
| 10 | `L` | `Sh` | `L` | No (completed) | - |
| 11 | `L` | `M` | `L` | No (completed) | - |
| 12 | `L` | `L` | `M` | No (completed) | - |
| 13 | `L` | `VL` | `Sh` | No (completed) | - |
