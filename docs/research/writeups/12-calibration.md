# Calibration: validation-only, with visible limited support

## Question

How are predicted probabilities made trustworthy, and what happens when an input
falls outside the data the calibrator was fit on?

## The problem

A model can discriminate well yet be miscalibrated: its 0.2 predictions might be
goals 30% of the time. Fixing this by fitting a calibrator on the test set would be
circular. And a calibrator fit on one region of inputs says nothing about inputs
far outside it.

## Approach

Proper scores (log loss, Brier) and a reliability table measure calibration
(`models.calibration`). A Platt calibrator is fit on validation data only and
applied to test predictions. Expected calibration error summarises the reliability
gaps. Out-of-support inputs are meant to produce a visible limited-support status
rather than a confident number.

## Evidence

Tests confirm the reliability table partitions all examples into bins and that Platt
scaling does not increase the expected calibration error on a miscalibrated set. The
demo reports the trained xG log loss against the base-rate predictor, and the
evaluation command reports log loss, Brier, and ECE together.

## Conclusion

Calibration is measured with proper scores and reliability, corrected only on
validation data, and reported alongside sample sizes, which is what gate G08
requires.
