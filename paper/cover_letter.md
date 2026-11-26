Editorial Office\
IEEE Transactions on Network and Service Management

Dear Editor,

Please consider the enclosed manuscript, “When Does Recalibration Help
Cellular Throughput Commitments? Accounting for Cost, Missingness, and
Abstention,” formatted in two-column `IEEEtran` journal style for
consideration in *IEEE Transactions on Network and Service Management*.

Centered on a practical empirical accounting methodology, reporting
checklist, and reusable open-source CLI tool (`audit_policy.py`), the
manuscript leads with our descriptive finding across 16 retrospective
physical campaign-dates and 26 held-out archive dates under frozen
predictors and fixed policies: mobile conditional upper violation risk
spans $`9\%`$–$`68\%`$ above nominal $`\alpha=0.10`$ while supported
measured throughput remains around $`1\%`$–$`3\%`$, aggregate contrasts
depend heavily on offer-count pooling weights ($`-23.41`$
vs. $`+0.37`$ pp), and sparse finite-sample bounds become vacuous on
$`36/40`$ evaluated cells. Separating equal-cluster and pooled-ratio
relative TOST equivalence at a $`\pm 50\%`$ baseline margin shows that
naive date-level equivalence largely fails or collapses under
three-campaign clustering sensitivity ($`G_{\text{eff}}=3.84/16`$
retrospective MARUR; $`6.73/26`$ held-out cap-40 PACER,
$`p=0.0071 \to 0.1153`$), leaving utility differences largely
inconclusive.

All evidence is retrospective from public archives, with no live field
validation, and it does not cover other devices, operators, measurement
tools, or closed-loop deployment. Repository source code is released
under the MIT License (`LICENSE`), and third-party public dataset terms
are documented separately without redistribution.

Sincerely,\
Md. Moazzem Hossain Majumder
