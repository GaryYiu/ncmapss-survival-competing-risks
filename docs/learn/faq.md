# "Why not just...?" 

**Why not just drop the two censored engines?**
Because they are the engines that lasted longest. Dropping them biases every estimate of lifetime downward, and with 25 engines two is 8% of the sample. Kaplan-Meier and Cox use them correctly at no cost: they count as at risk up to flight 100 and then leave without being counted as failures.

**Why not just predict RUL like everyone else?**
Because RUL cannot represent "more than 100 flights" (the censored engines read RUL = 0 at their last flight, indistinguishable from a failure), gives no interval, and gives no cause. The LSTM benchmark in this report does predict RUL, to within 9.6 flights, and ranks unseen engines exactly as well as a three-coefficient Cox model. What it cannot do is tell a planner the probability of failing from each cause over the next 20 flights.

**Why not use all 14 sensors as covariates?**
Eight and fifteen events support two or three coefficients, not fourteen (about ten events per coefficient is the rule). The sensors also measure one gas path and are strongly correlated, so they carry far fewer than fourteen independent pieces of information. PCA keeps 71% of their variance in two numbers.

**Why PCA rather than picking the two best sensors?**
Picking "the best" sensors on 25 engines is itself a form of over-fitting: whichever two happen to look best in this sample would be chosen. PCA is fitted without looking at the outcome, so it does not use up any of the events.