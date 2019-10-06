
from builtins import map as MAP
from builtins import zip as ZIP
from builtins import filter as FILTER

map = lambda *pars : list(MAP(*pars))
zip = lambda *pars : list(ZIP(*pars))
filter = lambda *pars : list(FILTER(*pars))
apply = lambda foo,*pars,**kargs : foo(*pars, **kargs)

if __name__ == "__main__":
	test = [1,2,3,4,5]

	print ('Old -> ', map(str,test))
	print ('New -> ', MAP(str,test))

	print ('Old -> ', zip(test,test))
	print ('New -> ', ZIP(test,test))

	print ('Old -> ', filter(str,test))
	print ('New -> ', FILTER(str,test))