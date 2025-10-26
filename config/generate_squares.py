# generate_squares.py
for i in range(250):
    row = i // 50
    col = i % 50
    print(f'<use href="#stress_square_def" x="{col*20}" y="{row*20}" id="sq_{i}" '
          f'data-datapoint="StressTest@DP_{i}" data-animation="stress_square"/>')