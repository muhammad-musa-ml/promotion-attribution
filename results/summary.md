# Results

Seeds 1 to 10, generator settings {'users': 2000, 'jobs': 30, 'promoted': 10, 'considered': 3}. Each cell is the mean over seeds with the lowest and highest seed in brackets. Events per seed: 2611 to 2755. Applications caused by a promotion per seed: 161 to 199.

## Methods

| method | credited / caused | precision | recall |
| --- | --- | --- | --- |
| period share | 3.35 (3.06 to 3.98) | 29.2% (24.4% to 32.0%) | 97.2% (95.5% to 99.5%) |
| windows in arrival order (click 7d, view 24h) | 1.43 (1.31 to 1.62) | 65.6% (58.2% to 70.3%) | 93.7% (91.5% to 98.3%) |
| attribute (click 7d, view 24h) | 1.44 (1.32 to 1.57) | 69.8% (63.6% to 75.9%) | 100.0% (100.0% to 100.0%) |

## Length of the view window (click window fixed at 7 days)

| method | credited / caused | precision | recall |
| --- | --- | --- | --- |
| attribute (click 7d, view off) | 0.66 (0.61 to 0.70) | 100.0% (100.0% to 100.0%) | 65.7% (60.9% to 69.7%) |
| attribute (click 7d, view 1h) | 0.67 (0.62 to 0.72) | 97.7% (95.2% to 99.2%) | 65.7% (60.9% to 69.7%) |
| attribute (click 7d, view 6h) | 0.85 (0.80 to 0.91) | 87.0% (83.1% to 89.7%) | 74.3% (67.4% to 78.7%) |
| attribute (click 7d, view 24h) | 1.44 (1.32 to 1.57) | 69.8% (63.6% to 75.9%) | 100.0% (100.0% to 100.0%) |
| attribute (click 7d, view 72h) | 2.32 (2.17 to 2.61) | 43.2% (38.3% to 46.1%) | 100.0% (100.0% to 100.0%) |

credited / caused is the number of credit entries divided by the number of applications the generator made because of a promotion; 1.00 means the right total, above 1 means the report claims more than the promotions caused.
