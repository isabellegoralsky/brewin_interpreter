known issues:
- test_func_with_lambda2
- test_bad_func4

- lambda creates closures for all vars even if they aren't used within the lambda, leading to some incorrect results
    (lines 183-185)