# Analytical goals

Every method in this program carries five numbers that say what it is held
to: the within-subject and between-subject biological variation, the
allowable imprecision, the allowable bias and the allowable total error.
This is where they come from.

## The formulae

They are the ones the EFLM Task Group for the Biological Variation Database
sets out in *Analytical performance specifications based on biological
variation data* (Sandberg et al., Clin Chem Lab Med, 2024), which is also
the paper to read for what they can and cannot be used for.

    CVa  = 0.5 × CVi                     allowable imprecision
    bias = 0.25 × √(CVi² + CVg²)         allowable bias
    TEa  = 1.65 × CVa + bias             allowable total error, one sided 95%

The coverage factor is the `zscore` setting: 1.65 for a one-sided 95%, 1.96
for a two-sided one, 2 for the conventional k = 2. Change it in
`biovarase.ini` and every total error in the program follows.

`qc.py` computes them, one method each, and the tests check them.

## Two kinds of measurand, two kinds of goal

**An endogenous analyte** - a hormone, a vitamin, a catecholamine - varies
around a set point of its own, and that variation is what the method has to
be small against. Its goals come from the formulae above.

**A drug does not.** The concentration of carbamazepine in a patient is what
the dose, the absorption and the metabolism make it: asking for its
within-subject biological variation is asking a question with no answer, and
a number written there would be invented. For the drugs the goal is the
state of the art - what competent laboratories achieve, as external quality
assessment schemes measure it - expressed directly as an allowable total
error, with the imprecision and the bias read back out of it so that the two
kinds of goal can be compared on the same chart.

In the sample database this is why carbamazepine and tacrolimus have `cvw`
and `cvb` at zero and a total error of 20%, while cortisol carries 20.9 and
45.6 and gets a total error of 29.8% out of them.

## The values in the sample database

Biological variation, for the endogenous analytes. The figures are the
published ones, rounded; for a laboratory using this program in earnest, the
EFLM database is the place to take them from, because they are revised as
studies are appraised.

| Analyte | CVi % | CVg % |
|---|---|---|
| Cortisol | 20.9 | 45.6 |
| Cortisone | 21.0 | 35.0 |
| 11-Deoxycortisol | 20.0 | 40.0 |
| Testosterone | 10.0 | 28.0 |
| Androstenedione | 12.0 | 30.0 |
| 17-OH-Progesterone | 20.0 | 38.0 |
| DHEA-S | 9.0 | 30.0 |
| Aldosterone | 29.0 | 40.0 |
| Vitamin A | 12.0 | 20.0 |
| Vitamin E | 10.0 | 20.0 |
| Vitamin B1 | 15.0 | 25.0 |
| Vitamin B6 | 15.0 | 25.0 |
| Adrenaline | 30.0 | 42.0 |
| Noradrenaline | 20.0 | 35.0 |
| Dopamine | 25.0 | 40.0 |
| Metanephrine | 20.0 | 32.0 |
| Normetanephrine | 18.0 | 30.0 |
| CDT | 4.5 | 12.0 |

State of the art, for the substances that have no biological variation:

| Panel | TEa % |
|---|---|
| Antiepileptics | 20 |
| Immunosuppressants | 20 |
| Drugs of abuse | 25 |

## Where they are seen

In the main window, `TEa%` sits in the *Lot* box and `TE%` in *Performance*:
what the analyte allows, and what this series is doing. When the second
passes the first, the method is missing its goal whatever the Westgard rules
say - the rules are about control, the goals are about fitness for purpose,
and a method can be in control and not good enough.

## Sources

- Sandberg S. et al., *Analytical performance specifications based on
  biological variation data - considerations, strengths and limitations*,
  Clin Chem Lab Med 2024. https://doi.org/10.1515/cclm-2024-0108
- EFLM Biological Variation Database. https://biologicalvariation.eu
- Fraser C.G., *Biological Variation: From Principles to Practice*, AACC
  Press, 2001.
- ISO/TS 20914:2019, practical guidance for the estimation of measurement
  uncertainty, for the expanded uncertainty shown as `U%`.
