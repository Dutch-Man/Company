#Test002.py
import numpy as np
def function(k1,x1,y1,k2,x2,y2):
    a = [[k1,-1],[k2,-1]]
    b = [k1*x1-y1,k2*x2-y2]
    a = np.array(a)
    b = np.array(b)
    x = np.linalg.solve(a,b)
    print x
if __name__ == "__main__":
    function(1,2,3,4,5,6)