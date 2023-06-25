from backend.ml_utils import predict
import sys

# Access command-line arguments
user_id = sys.argv[1]

if __name__ == "__main__":
    print(predict(user_id))