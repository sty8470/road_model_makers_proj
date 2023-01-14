import numpy as np

import matplotlib.pyplot as plt
"""
x_coor = [ 0.         , 5.64313586 ,17.22662278, 27]
y_coor = [0.     ,    0.       ,  0.22857455, 0.6]
series, misc_fit_result=np.polynomial.polynomial.Polynomial.fit(
                x_coor,
                y_coor,
                3,
                full=True
            )
poly_out = series.convert().coef
print(series)
print(misc_fit_result)
print("coef = ",poly_out)


series2, misc_fit_result2=np.polynomial.polynomial.polyfit(
                x_coor,
                y_coor,
                3,
                full=True
            )

coef =  series.convert().coef
xnew = np.linspace(0, 20, num=30, endpoint=True)
"""

#x_coord_new = [x_coord[0],x_coord[1],x_coord[-2],x_coord[-1]]
#y_coord_new =  [y_coord[0],y_coord[1],y_coord[-2],y_coord[-1]]

#y_coordthr = [ 0.00000000e+00,  4.44089210e-16, -2.14545189e+01, -7.63732622e+01]
#x_coordthr = [  0.  ,         5.3458208 ,  115.22681646, 204.73574355]





#######################################ref length ################################################
length = 3
tnew = np.linspace(0, length, num=100, endpoint=True)

def x_bezier(x_coord, t , length):
    return ((length-t)**3)*x_coord[0]/(length**3) + 3*t*((length-t)**2)*x_coord[1]/(length**3) + 3*(t**2)*(length-t)*x_coord[2]/(length**3) + (t**3)*x_coord[3]/(length**3)

def y_bezier(y_coord, t , length):
    return ((length-t)**3)*y_coord[0]/(length**3) + 3*t*((length-t)**2)*y_coord[1]/(length**3) + 3*(t**2)*(length-t)*y_coord[2]/(length**3) + (t**3)*y_coord[3]/(length**3)



x_coor = [ 0.         , 5.64313586 ,17.22662278, 27]
y_coor = [0.     ,    0.       ,  0.22857455, 0.6]

x_coor3 = x_coor[-1] - ( y_coor[-1]/(y_coor[-1] - y_coor[-2])*(x_coor[-1]-x_coor[-2] )    )

line_x_coor_new =   [x_coor[0], x_coor[1], x_coor3 -1 , x_coor[-1]] 
line_y_coor_new =   [y_coor[0],0, -0.1 , y_coor[-1]] 

# plt.plot(x_coor, y_coor, 'o', x_bezier(x_coor, tnew, length),  y_bezier(y_coor, tnew, length), '-')
# plt.title("length reference included ")
# plt.show()
# plt.plot(x_coor, y_coor, 'o', x_bezier(line_x_coor_new, tnew, length),  y_bezier(line_y_coor_new, tnew, length), 'r','-')
# plt.title("length reference included ")
# plt.show()
# plt.plot(x_coor, y_coor, 'o', x_bezier(x_coor, tnew, length),  y_bezier(y_coor, tnew, length), '-', x_bezier(line_x_coor_new, tnew, length),  y_bezier(line_y_coor_new, tnew, length), 'r','-')
# plt.title("length reference included ")
# plt.show()
######################################################################################################










###############################all point ####################################

length = 1

x_coord = [  0.  ,         5.3458208 ,  13.00641857 , 20.84756242,  26.68499872,
  34.53780695, 42.63210466 , 48.68625813 , 54.72279319 , 60.73480721,
  66.72688264 , 73.93579904,  81.09532417 , 88.93245657 , 94.77518671,
 102.36405325, 109.73935337, 115.22681646, 122.48413397, 129.66505849,
 134.99344367, 142.30027987, 147.7124553,  154.64250033, 160.91744797,
 165.74467512, 170.87080158 ,177.6035898,  182.57113339, 187.46390998,
 193.87293902, 198.58082586, 204.73574355]

y_coord = [ 0.00000000e+00,  4.44089210e-16, -1.61828210e-01,-5.06086661e-01,
 -9.40019754e-01 ,-1.68808327e+00, -2.64032055e+00, -3.50016457e+00,
 -4.47293806e+00 ,-5.57993873e+00, -6.80169851e+00, -8.42387898e+00,
 -1.02200183e+01 ,-1.24166007e+01, -1.41880766e+01, -1.66892851e+01,
 -1.93454982e+01, -2.14545189e+01, -2.44270634e+01, -2.76006862e+01,
 -3.01038092e+01, -3.37260062e+01, -3.65741917e+01, -4.04346195e+01,
 -4.41182831e+01, -4.70960386e+01, -5.04187554e+01, -5.50028109e+01,
 -5.85577576e+01 ,-6.22108043e+01, -6.72258360e+01, -7.10879484e+01,
 -7.63732622e+01]

x_coord3 = x_coord[-1] - ( y_coord[-1]/(y_coord[-1] - y_coord[-2])*(x_coord[-1]-x_coord[-2] )    )

line_x_coord_new =   [x_coord[0], x_coord[1], x_coord3 , x_coord[-1]] 
line_y_coord_new =   [y_coord[0],0, 0 , y_coord[-1]] 

line_x_coord_new2 =   [x_coord[0], x_coord[1], x_coord3-1.0e+01  , x_coord[-1]] 
line_y_coord_new2 =   [y_coord[0],0, +7 , y_coord[-1]] 


def coeff_x_bezier(line_x_coord, length,   t):
    x_coord = line_x_coord
    x_coord3 = x_coord[-1] - ( y_coord[-1]/(y_coord[-1] - y_coord[-2])*(x_coord[-1]-x_coord[-2] )    )

    line_x_coord_new =   [x_coord[0], x_coord[1], x_coord3 , x_coord[-1]] 
    line_y_coord_new =   [y_coord[0],0, 0 , y_coord[-1]] 



    dU = line_x_coord[3]/(length**3) -3*line_x_coord[2]/(length**3) +3*line_x_coord[1]/(length**3)
    cU = 3*line_x_coord[2]/(length**3)-6*line_x_coord[1]/(length**3)
    bU = 3*line_x_coord[1]/(length**3)
    
    return  bU*(t**1) + cU*(t**2) + dU*(t**3)

def coeff_y_bezier(line_y_coord,length,  t):
    
    dV = line_y_coord[3]/(length**3)-3*line_y_coord[2]/(length**3)
    cV = 3*line_y_coord[2]/(length**3)
    
    return  cV*(t**2) + dV*(t**3)



tnew = np.linspace(0, length, num=100, endpoint=True)

# plt.plot(x_coord, y_coord, 'o', coeff_x_bezier(line_x_coord_new, length,  tnew),  coeff_y_bezier(line_y_coord_new, length, tnew), '-')
# plt.title("all point ")
# plt.show()

# plt.plot(x_coord, y_coord, 'o', coeff_x_bezier(line_x_coord_new2, length,  tnew),  coeff_y_bezier(line_y_coord_new2, length, tnew),'r', '-')

# plt.show()

# plt.plot(x_coord, y_coord, 'o', coeff_x_bezier(line_x_coord_new, length,  tnew),  coeff_y_bezier(line_y_coord_new, length, tnew), '-', coeff_x_bezier(line_x_coord_new2, length,  tnew),  coeff_y_bezier(line_y_coord_new2, length, tnew), 'r','-')
# plt.title("all point ")
# plt.show()
###################################################################################################
"""


"""

x_coord = [  0.  ,         5.3458208 ,  13.00641857 , 20.84756242,  26.68499872,
  34.53780695, 42.63210466 , 48.68625813 , 54.72279319 , 60.73480721,
  66.72688264 , 73.93579904,  81.09532417 , 88.93245657 , 94.77518671,
 102.36405325, 109.73935337, 115.22681646, 122.48413397, 129.66505849,
 134.99344367, 142.30027987, 147.7124553,  154.64250033, 160.91744797,
 165.74467512, 170.87080158 ,177.6035898,  182.57113339, 187.46390998,
 193.87293902, 198.58082586, 204.73574355]

y_coord = [ 0.00000000e+00,  4.44089210e-16, -1.61828210e-01,-5.06086661e-01,
 -9.40019754e-01 ,-1.68808327e+00, -2.64032055e+00, -3.50016457e+00,
 -4.47293806e+00 ,-5.57993873e+00, -6.80169851e+00, -8.42387898e+00,
 -1.02200183e+01 ,-1.24166007e+01, -1.41880766e+01, -1.66892851e+01,
 -1.93454982e+01, -2.14545189e+01, -2.44270634e+01, -2.76006862e+01,
 -3.01038092e+01, -3.37260062e+01, -3.65741917e+01, -4.04346195e+01,
 -4.41182831e+01, -4.70960386e+01, -5.04187554e+01, -5.50028109e+01,
 -5.85577576e+01 ,-6.22108043e+01, -6.72258360e+01, -7.10879484e+01,
 -7.63732622e+01]

x_linear = x_coord
y_linear = [ 0 for i in range(len(x_coord))]

# x_coord3 = x_linear[-1] - ( y_linear[-1]/(y_linear[-1] - y_linear[-2])*(x_linear[-1]-x_linear[-2] )    )

x_linear_new =   [x_linear[0], x_linear[1], x_linear[-2] , x_linear[-1]] 
y_linear_new =   [y_linear[0],0, 0 , y_linear[-1]] 

#x_linear_new2 =   [x_linear[0], x_linear[1], x_coord3-1.0e+01  , x_linear[-1]] 
#y_linear_new2 =   [y_linear[0],0, +7 , y_linear[-1]] 


# plt.plot(x_linear, y_linear, 'o', coeff_x_bezier(x_linear_new, length,  tnew),  coeff_y_bezier(y_linear_new, length, tnew), '-')
# plt.title("all point ")
# plt.show()
"""
# plt.plot(x_linear, y_linear, 'o', coeff_x_bezier(x_linear, length,  tnew),  coeff_y_bezier(y_linear, length, tnew),'r', '-')

# plt.show()

# plt.plot(x_linear, y_linear, 'o', coeff_x_bezier(x_linear, length,  tnew),  coeff_y_bezier(y_linear, length, tnew), '-', coeff_x_bezier(x_linear, length,  tnew),  coeff_y_bezier(y_linear, length, tnew), 'r','-')
# plt.title("all point ")
#plt.show()

"""


x_data = np.linspace(0, 200, num=100)

y_data =  np.sin(0.02 * x_data) #+ np.random.normal(size=200)


x_data_new =   [x_data[0], x_data[1], x_data[-2] , x_data[-1]] 
y_data_new =   [y_data[0],y_data[1],y_data[-2] , y_data[-1]] 


x_coord3 = x_coord[-1] - ( y_coord[-1]/(y_coord[-1] - y_coord[-2])*(x_coord[-1]-x_coord[-2] )    )

line_x_coord_new =   [x_coord[0], x_coord[1], x_coord3 , x_coord[-1]] 
line_y_coord_new =   [y_coord[0],0, 0 , y_coord[-1]] 

line_x_coord_new2 =   [x_coord[0], x_coord[1], x_coord3-1.0e+01  , x_coord[-1]] 
line_y_coord_new2 =   [y_coord[0],0, +7 , y_coord[-1]] 





# plt.figure(figsize=(6, 4))
# plt.plot(x_data, y_data, 'o', coeff_x_bezier(x_data_new, length,  tnew),  coeff_y_bezier(y_data_new, length, tnew), '-')

# plt.show()
# plt.plot(x_coord, y_coord, 'o', coeff_x_bezier(line_x_coord_new2, length,  tnew),  coeff_y_bezier(line_y_coord_new2, length, tnew),'r', '-')

# plt.show()

# plt.plot(x_coord, y_coord, 'o', coeff_x_bezier(line_x_coord_new, length,  tnew),  coeff_y_bezier(line_y_coord_new, length, tnew), '-', coeff_x_bezier(line_x_coord_new2, length,  tnew),  coeff_y_bezier(line_y_coord_new2, length, tnew), 'r','-')
# plt.title("all point ")
# plt.show()





coord0629 = [[117.90703172446229, -105.2613493828103, -10.480660871260625], 
[117.3093749327818, -109.48424782976508, -10.444432129684003],
 [116.5900293183513, -113.18641521688551, -10.41144328255342], 
 [115.8924793577171, -116.12094299588352, -10.377952624896295], 
 [114.419777218136, -121.1871110284701, -10.3184361688389], 
 [112.47793208278017, -126.49207207094878, -10.25598592971005], 
 [110.18226977123413, -131.64945691265166, -10.180060876630819],
  [108.33999347849749, -135.21445831656456, -10.123353477822207],
   [107.34825712407473, -136.95774598885328, -10.093762464543715],
    [105.24553793901578, -140.371675808914, -10.033237855500602], 
    [104.12778009485919, -142.03489067219198, -10.004364985422797],
     [101.78282595041674, -145.2818204164505, -9.945793960743856],
      [100.54710066120606, -146.85722746048123, -9.911350085553863],
       [98.14015310560353, -149.73436220176518, -9.851654876279667],
        [96.87903689290397, -151.1223706351593, -9.819103489836891],
         [94.28334870166145, -153.82589595019817, -9.756239157662606],
          [92.9296349491342, -155.12083542346954, -9.726562510039912],
           [90.15342382155359, -157.63265622407198, -9.655383856769788],
            [87.59520812961273, -159.75785835832357, -9.599892171459658],
             [82.91161291592289, -163.20751153118908, -9.497898522343633],
              [77.99609495152254, -166.3191370870918, -9.393695902478044],
               [72.71330421383027, -169.14456027001143, -9.283485943806397],
                [69.0731362849474, -170.80443060025573, -9.208902039311226],
                 [66.75958458386594, -171.76370295137167, -9.162349250785155], 
                 [61.77372347400524, -173.54812704306096, -9.066678893441178],
                  [56.61200311523862, -175.0011000400409, -8.962260461768778], 
                  [51.356946978427004, -176.11915300041437, -8.860215818519805],
                   [47.313015257939696, -176.7514268392697, -8.769508011467849],
                    [43.798722783627454, -177.1259352164343, -8.698135777951109],
                     [40.60700074327178, -177.3192737363279, -8.617533314254047],
                      [34.88373996352311, -177.38011517282575, -8.48851995046357], 
                      [32.190964570385404, -177.26695245783776, -8.409093938080105], 
                      [28.159189469181, -176.95220472104847, -8.298280681725373], 
                      [22.812362784403376, -176.24104969669133, -8.149110936510624],
                       [19.170465401373804, -175.5434757359326, -8.045094927060177],
                        [16.953797294583637, -175.0306155225262, -7.980082014988284],
                         [14.023478798917495, -174.2504172809422, -7.886582552531479], 
                         [11.1271319888765, -173.35835606697947, -7.790713605666099],
                          [6.149384018499404, -171.54219700116664, -7.630369921761826], 
                          [1.4447888205759227, -169.4724257895723, -7.46474106406788],
                           [-3.381502127740532, -166.97578481864184, -7.291525950927564],
                            [-5.984206762514077, -165.4533118158579, -7.1925495009422775],
                             [-8.802013367239852, -163.64696865994483, -7.0808987858169985],
                              [-13.414038561284542, -160.32954940013587, -6.8936757000485045],
                               [-18.025564453098923, -156.48172097280622, -6.693345387995919], 
                               [-20.224384322355036, -154.44015483930707, -6.592023513309073],
                                [-22.33860967855435, -152.3127301093191, -6.487459661508524]] 

coord0629 = np.array(coord0629)

def coordinate_transform( angle, line):
    rotation = np.array(((np.cos(angle), -np.sin(angle)),
    (np.sin(angle), np.cos(angle))))
        
    transform_line = np.zeros((len(line), 2))

    for indx, point in enumerate(line):
        original_pt = np.array([point[0], point[1]])
        transform_pt = rotation.dot(original_pt)
        transform_line[indx] = transform_pt

    return transform_line                        



lane_vector = coord0629[0:-1,0:2]
        
x_init = lane_vector[0][0]
y_init = lane_vector[0][1]
init_coord = np.array([x_init, y_init])
line_moved_origin = lane_vector - init_coord


u = line_moved_origin[1][0] 
v = line_moved_origin[1][1] 

heading = np.arctan2(v, u)  



inv_heading = (-1) * heading
rotated_line = coordinate_transform(inv_heading, line_moved_origin)
line_x_coord = rotated_line[:,0]
line_y_coord = rotated_line[:,1]

# plt.plot(line_x_coord, line_y_coord, 'o')
# plt.show()

##########################################################################
# print("first point", line_x_coord[0], line_y_coord[0])
# print("last point", line_x_coord[-1], line_y_coord[-1])
# slope_x = line_x_coord[-1] -line_x_coord[0]
# slope_y = line_y_coord[-1] -line_y_coord[0]
# heading2 = -np.arctan2(slope_y, slope_x)  

# lastpoint =  coordinate_transform(heading2,[[line_x_coord[-1], line_y_coord[-1]]])

# print("lastpoint", lastpoint)

# slope_x = line_x_coord[-1] -line_x_coord[0]
# slope_y = line_y_coord[-1] -line_y_coord[0]
# heading2 = -np.arctan2(slope_y, slope_x)  
# rotated_line2 = coordinate_transform(heading2,rotated_line )

# print(rotated_line2[-1])



# line_x_coord2 = rotated_line2[:,0]
# line_y_coord2 = rotated_line2[:,1]
# plt.plot(line_x_coord2, line_y_coord2, 'o')
# plt.show()
# maxpoint = sorted(rotated_line2,reverse = True, key=lambda rotated_line2: rotated_line2[1])[0]
# print("maxpoint" ,maxpoint)

# far_point = coordinate_transform(-heading2,[maxpoint] )
# print("far point" ,far_point)

# plt.plot(line_x_coord, line_y_coord, 'o', far_point[0][0], far_point[0][1], "r")
# plt.show()


def length(last_point,  point):
    b = np.sqrt(last_point[0]**2+ last_point[1]**2)
    a = abs(last_point[1]*point[0] - last_point[0]*point[1])
    return a/b


def whole_length(data_set):
    length = 0
    for j in range(1, len(data_set)):
        length +=np.sqrt( (data_set[j][0] -data_set[j-1][0])**2 +(data_set[j][1] -data_set[j-1][1])**2)
    
    #print(length)
    return length


def till_length(data):
    till_length = 0 
    for j  in range(1, len(data)):
        till_length +=np.sqrt((data[j][0] -data[j-1][0])**2 +(data[j][1] -data[j-1][1])**2)
        #print("till_length ",till_length)
    return till_length



length = 1
tnew = np.linspace(0, length, num=100, endpoint=True)

def x_bezier(x_coord, t , length):
    return ((length-t)**3)*x_coord[0]/(length**3) + 3*t*((length-t)**2)*x_coord[1]/(length**3) + 3*(t**2)*(length-t)*x_coord[2]/(length**3) + (t**3)*x_coord[3]/(length**3)

def y_bezier(y_coord, t , length):
    return ((length-t)**3)*y_coord[0]/(length**3) + 3*t*((length-t)**2)*y_coord[1]/(length**3) + 3*(t**2)*(length-t)*y_coord[2]/(length**3) + (t**3)*y_coord[3]/(length**3)


sinecurve = [[1094.80016049,  277.20327356,  -14.60047421],
       [1085.24376061,  277.81118191,  -14.70457571],
       [1073.76353337,  278.38147427,  -14.78966496],
       [1062.27752257,  278.77875927,  -14.8831766 ],
       [1050.5710465 ,  278.97607242,  -14.94779196],
       [1038.64964393,  278.95666431,  -15.00539966],
       [1026.73507669,  278.72116392,  -15.03647685],
       [1014.82866039,  278.25733786,  -15.08423577],
       [1002.92494501,  277.58227264,  -15.13233249],
       [ 991.03148439,  276.70652704,  -15.16151652],
       [ 979.16129778,  275.62183724,  -15.17234978],
       [ 967.3056015 ,  274.33604977,  -15.16204268],
       [ 955.47199674,  272.86034391,  -15.13018349],
       [ 943.66855418,  271.1870395 ,  -15.0743667 ],
       [ 931.89859594,  269.31639648,  -15.01547449],
       [ 924.07603652,  267.9512886 ,  -14.96749671],
       [ 912.37451383,  265.72118002,  -14.90802665],
       [ 900.71180651,  263.28372512,  -14.85113758],
       [ 884.23835872,  259.54714992,  -14.76413246],
       [ 872.70583221,  256.6063962 ,  -14.71986119],
       [ 861.3898514 ,  253.54077133,  -14.66261816],
       [ 848.63326051,  249.85653581,  -14.61575888],
       [ 763.24772432,  224.64546082,  -14.22528576],
       [ 664.73263308,  195.27839753,  -13.87660533],
       [ 647.85286345,  190.40173372,  -13.83087322],
       [ 630.38901059,  185.65850127,  -13.76651938],
       [ 618.69520865,  182.67694245,  -13.71779127],
       [ 603.05301376,  178.93190327,  -13.64136392],
       [ 589.67171176,  175.88027117,  -13.57086378],
       [ 572.48411927,  172.1954997 ,  -13.48691709],
       [ 555.38009501,  168.80289757,  -13.42717331],
       [ 542.11466321,  166.32223388,  -13.36636604],
       [ 526.28528089,  163.58818742,  -13.30813302],
       [ 514.39256533,  161.67872529,  -13.25438496],
       [ 502.86038851,  159.9587149 ,  -13.20240855],
       [ 485.57530513,  157.60512009,  -13.11618794],
       [ 469.64793534,  155.66453628,  -13.028485  ],
       [ 455.68773422,  154.12473893,  -12.95975229],
       [ 439.6960011 ,  152.58779931,  -12.88142268],
       [ 427.69093323,  151.60645651,  -12.82728666],
       [ 412.10286511,  150.47396748,  -12.76852845],
       [ 398.45269017,  149.66837112,  -12.69655313],
       [ 382.56608889,  148.9363741 ,  -12.61758875],
       [ 368.5220081 ,  148.45745581,  -12.55686069],
       [ 356.47169084,  148.18367555,  -12.50704407],
       [ 340.40693644,  148.02766847,  -12.46864142],
       [ 328.51913693,  148.06677438,  -12.43057141],
       [ 316.94192886,  148.25768411,  -12.38863538],
       [ 297.65794086,  148.75724848,  -12.27371811],
       [ 282.23088457,  149.3232712 ,  -12.17698675]]
from_point = [1104.2943614280084, 276.46074931230396, -14.485615864669][0:2]
to_point = [268.3677034773282, 150.02240425068885, -12.116556878492588][0:2]



sinecurve = [[-1308.40155651,   348.19180213,    -4.51526538],
       [-1236.10340874,   337.81480109,    -4.57149295],
       [-1206.8996551 ,   333.7437647 ,    -4.57884085],
       [-1140.64887195,   324.19841993,    -4.5573518 ],
       [-1078.37441439,   315.36532948,    -4.60218431],
       [ -965.25227797,   298.99329173,    -4.82074186],
       [ -897.6643395 ,   289.29192884,    -5.0893014 ],
       [ -847.52509399,   282.1873165 ,    -5.31514868]]

from_point = [-1391.59419105,   360.21145239,    -4.44265666][:2]
to_point = [-787.15987923,  273.5388691 ,   -5.56107632][:2]



# 'bd167502-f9a8-4704-95c1-31c87003c693'
# sinecurve = 'bd167502-f9a8-4704-95c1-31c87003c693'
# sinecurve = [[1368.70552906, -416.99646695,  -19.78814563],
#        [1269.80658625, -364.91173879,  -20.35166089],
#        [1263.37694345, -361.35967997,  -20.36911567],
#        [1259.86541497, -359.29168374,  -20.38534108],
#        [1255.19993452, -356.1435862 ,  -20.3898598 ]]
# to_point = [1251.5576389728813, -353.29671528283507, -20.382615073691454][0:2]
# from_point =[1400.0751115010353, -433.5858238907531, -19.53108696270823][0:2]

################################################################################
# 333

# sinecurve =[2244.94063124, 1099.0837583 ,   30.14255952],
#        [2235.70336537, 1095.52002633,   29.92042958],
#        [2226.50200559, 1091.84529434,   29.70715384]]

# to_point  =[2226.50200559, 1091.84529434,   29.70715384][0:2]
# from_point =[2255.31656333, 1102.93412477,   30.39219099][0:2]

###################################################################
# 111

# sinecurve =[[2380.09661889, 1142.32133385,   32.76929304],
#        [2320.34823666, 1123.88690343,   31.5660681 ],
#        [2295.63369455, 1116.09495804,   31.15958552],
#        [2283.28166076, 1112.35470075,   30.94623752]]


# to_point  =[2274.8471884 , 1109.70213754,   30.79553228][0:2]
# from_point = [2457.21344938, 1165.9790866 ,   34.61032539][0:2]
# road_aft_to_point = [2268.20809092, 1107.49474707,   30.66960287][0:2]
# road_pre_from_point = [2466.69887564, 1168.9043555 ,   34.84691334][0:2]

##############################################################
# 222

# sinecurve =[[2283.28166076, 1112.35470075,   30.94623752],
#        [2274.8471884 , 1109.70213754,   30.79553228],
#        [2268.20809092, 1107.49474707,   30.66960287],
#        [2255.31656333, 1102.93412477,   30.39219099],
#        [2244.94063124, 1099.0837583 ,   30.14255952]]


# to_point  =[2235.70336537, 1095.52002633,   29.92042958][0:2]
# from_point = [2295.63369455, 1116.09495804,   31.15958552][0:2]

#####################################################################
# sinecurve = [[1886.3010896 ,  179.41460166,  -17.77732948],
#        [1887.7259423 ,  189.03612985,  -17.73002126],
#        [1888.66219432,  194.7966173 ,  -17.70959814],
#        [1890.73947796,  206.28291397,  -17.64133711],
#        [1892.67652687,  215.80566938,  -17.59819856],
#        [1894.34374532,  223.39538974,  -17.56570315],
#        [1895.5860199 ,  228.72697961,  -17.547053  ],
#        [1897.82010566,  237.71230113,  -17.50573593],
#        [1899.78016608,  245.12069894,  -17.48637252],
#        [1902.40263091,  254.44918428,  -17.4478015 ],
#        [1906.37454517,  267.66290409,  -17.39975429],
#        [1911.26879731,  282.64720065,  -17.32262605],
#        [1916.54496564,  297.49327623,  -17.24465404],
#        [1921.45553938,  310.36830775,  -17.18939734],
#        [1925.12944535,  319.50349012,  -17.15032355],
#        [1927.4071472 ,  324.95167149,  -17.13594521],
#        [1929.73865187,  330.37737343,  -17.1091296 ],
#        [1934.5902363 ,  341.28431336,  -17.06866603],
#        [1938.82218424,  350.34428122,  -17.03399946],
#        [1941.43655725,  355.74289429,  -17.00651626],
#        [1944.10741455,  361.11240596,  -16.99711696],
#        [1948.68502328,  369.99616187,  -16.94763351],
#        [1955.35370619,  382.28299416,  -16.87326859],
#        [1960.32352135,  390.93753665,  -16.83417209],
#        [1963.39416255,  396.07535485,  -16.8148529 ],
#        [1966.53155212,  401.17127913,  -16.79732577],
#        [1970.82122413,  407.8975197 ,  -16.78774153]]

# from_point =[1884.73814411,  167.52594326,  -17.83707669][:2]
# to_point = [1978.00057909,  419.04280781,  -16.76437681][:2]



# u =  line_moved_origin[1][0] 
# v = line_moved_origin[1][1] 
# heading = np.arctan2(v, u)  
# inv_heading = (-1) * heading

# rotated_line = coordinate_transform(inv_heading, line_moved_origin)
# line_x_coord = rotated_line[:,0]
# line_y_coord = rotated_line[:,1]

# min = whole_length(rotated_line)

# for i  in range(2, len(rotated_line)):
     
#     if  np.abs(till_length(rotated_line[:i])- whole_length(rotated_line)/2) :
#         min = np.abs(till_length(rotated_line[:i])- whole_length(rotated_line)/2)
        
#         maxpoint = rotated_line[i]


# print("max point !!!!!!!!!!!!!!!", maxpoint)

# #maxpoint = [350,80]
# a=rotated_line[1][1]/rotated_line[1][0]
# b= (rotated_line[-1][1] - rotated_line[-2][1])/(rotated_line[-1][0] - rotated_line[-2][0])

# x_t =  (8*(maxpoint[1]- a*maxpoint[0])  + rotated_line[-1][0]*(a+3*b) - 4*rotated_line[-1][1])/(3*(b-a))   # (1/2)*rotated_line[-1][0]  + x_k -2*maxpoint[0]
# x_k = (8*maxpoint[0] -3*x_t -  rotated_line[-1][0])/3

# y_k = a*x_k
# y_t = b*(x_t- rotated_line[-1][0])+ rotated_line[-1][1]


#  plt.plot(line_x_coord, line_y_coord, 'o')
# # print("y_ height _ ",line_y_coord)
# #plt.plot(maxpoint[0],maxpoint[1], 'o')
# plt.show()


# plt.plot([x_k, x_t],[y_k,y_t], 'o' )
# plt.plot(line_x_coord, line_y_coord, 'o')
# plt.show()


# plt.plot(line_x_coord, line_y_coord, 'o', x_bezier([0,x_k,x_t,rotated_line[-1][0] ], tnew, length),  y_bezier([0, y_k,y_t, rotated_line[-1][1]], tnew, length), '-')

# plt.show()

#####################################boundary condition ###########################

sinecurve = np.array(sinecurve)
lane_vector = sinecurve[:,0:2]

plt.plot(lane_vector[:,0], lane_vector[:,1], 'o')
plt.plot(from_point[0], from_point[1], 'o')
# plt.plot(rotated_from_point_moved[0][0],rotated_from_point_moved[0][1],'o')


# plt.plot(road_aft_to_point[0],road_aft_to_point[1],'o')
# plt.plot(road_pre_from_point[0],road_pre_from_point[1],'o')
plt.plot(to_point[0],to_point[1],'o')
plt.show()


x_init = lane_vector[0][0]
y_init = lane_vector[0][1]
print(x_init, y_init,"init, pre")
# x_init = (lane_vector[0][0] +lane_vector[1][0]  + from_point[0])/3
# y_init = (lane_vector[0][1] +lane_vector[1][1]  + from_point[1])/3
# print(x_init, y_init,"init")




init_coord = np.array([x_init, y_init])
line_moved_origin = lane_vector - init_coord

from_point_moved = from_point - init_coord
to_point_moved =  to_point - init_coord 

# aft_to_point_moved = road_aft_to_point - init_coord
# pre_from_point_moved = road_pre_from_point - init_coord



from_u =  line_moved_origin[1][0] - from_point_moved[0]
from_v = line_moved_origin[1][1]  - from_point_moved[1]

from_u =  (line_moved_origin[1][0] + line_moved_origin[0][0])/2 - (from_point_moved[0] +  line_moved_origin[0][0])/2
from_v = (line_moved_origin[1][1] + line_moved_origin[0][1])/2  - (from_point_moved[1] +  line_moved_origin[0][1])/2

# from_u = (line_moved_origin[2][0] + line_moved_origin[1][0])/2 - (from_point_moved[0] +  pre_from_point_moved[0])/2
# from_v =  (line_moved_origin[2][1] + line_moved_origin[1][1])/2  - (from_point_moved[1] +  pre_from_point_moved[1])/2

to_u = line_moved_origin[-2][0] - to_point_moved[0]
to_v = line_moved_origin[-2][1]  - to_point_moved[1]


from_heading = np.arctan2(from_v, from_u) 
to_heading = np.arctan2(to_v, to_u)  
from_inv_heading = (-1) * from_heading

# rotated_aft_to_point_moved = coordinate_transform(from_inv_heading, [aft_to_point_moved])

# rotated_pre_from_point_moved = coordinate_transform(from_inv_heading, [pre_from_point_moved])

rotated_line = coordinate_transform(from_inv_heading, line_moved_origin)
rotated_from_point_moved = coordinate_transform(from_inv_heading, [from_point_moved])
rotated_to_point_moved = coordinate_transform(from_inv_heading, [to_point_moved])

x_last  = (rotated_to_point_moved[0][0] + rotated_line[-1][0] + rotated_line[-2][0])/3
y_last = (rotated_to_point_moved[0][1] + rotated_line[-1][1] + rotated_line[-2][1])/3
print(x_last, y_last ,"last")
print("rotated_from_point_moved",rotated_from_point_moved,"rotated_to_point_moved",rotated_to_point_moved)

line_x_coord = rotated_line[:,0]
line_y_coord = rotated_line[:,1]


# plt.plot(rotated_aft_to_point_moved[0][0], rotated_aft_to_point_moved[0][1], 'o')
# plt.plot(rotated_pre_from_point_moved[0][0], rotated_pre_from_point_moved[0][1], 'o')
plt.plot(line_x_coord, line_y_coord, 'o')
# plt.plot(rotated_from_point_moved[0][0], rotated_from_point_moved[0][1], 'o')
plt.plot(rotated_from_point_moved[0][0],rotated_from_point_moved[0][1],'o')
# plt.plot(rotated_line[])
# plt.plot(x_init, y_init, "x")
# plt.plot(x_last, y_last, "x")
middle_to_bound = [(rotated_to_point_moved[0][0] + rotated_line[-1][0])/2 , (rotated_to_point_moved[0][1] + rotated_line[-1][1])/2 ]
middle_to_bound_e = [(rotated_line[-2][0] + rotated_line[-1][0])/2 , (rotated_line[-2][1] + rotated_line[-1][1])/2 ]
# plt.plot(x_init, y_init, "o")
# plt.plot(middle_to_bound_e[0],middle_to_bound_e[1],'x')
# plt.plot(middle_to_bound[0],middle_to_bound[1],'x')
plt.plot(rotated_to_point_moved[0][0],rotated_to_point_moved[0][1],'o')
plt.show()





# min = whole_length(rotated_line)

# for i  in range(2, len(rotated_line)):
  
    
#     if till_length(rotated_line[:i])- whole_length(rotated_line)/2 >0 :
#         rate_a = np.abs(till_length(rotated_line[:i-1])- whole_length(rotated_line)/2)
#         rate_b = np.abs(till_length(rotated_line[:i-2])- whole_length(rotated_line)/2)
#         print("rate",rate_a, rate_b)
#         maxpoint =  [(rotated_line[i-1][0]*rate_a + rotated_line[i-2][0]*rate_b ) /(rate_a + rate_b) ,( rotated_line[i-1][1]*rate_a + rotated_line[i-2][1]*rate_b)  /(rate_a + rate_b) ]
#         middle_a = rotated_line[i-1]
#         middle_b = rotated_line[i-2]
#         break

#maxpoint= [(rotated_line[0][0]+rotated_line[-1][0])/2 , (rotated_line[0][1] + rotated_line[-1][1])/2]
# plt.plot(line_x_coord, line_y_coord, 'o')
# plt.plot(middle_a[0],middle_a[1],"o", middle_b[0],middle_b[1], "o")
# plt.plot(maxpoint[0],maxpoint[1], 'o')
# plt.show()
###############################################################################################################################

def poly(line_x_coord, line_y_coord, to_slope = 0):
    x = line_x_coord[-1]
    y = line_y_coord[-1]
    if to_slope ==0:
        to_slope = (line_y_coord[-1] - line_y_coord[-2]) / (line_x_coord[-1] - line_x_coord[-2])
    d =  ((to_slope- 2*(y/x))/(x**2) )
    c = y/(x**2) - d*x 
    coeff_out = np.array([c, d])
    
    return coeff_out

def curve_length(line_x_coord,coeff_out, half = True):
    x = 0
    y = 0 
    dx = line_x_coord[-1]/10000
    whole_length = 0
    for i  in range(10000):
        x_n = x + dx
        y_n = (coeff_out[0]*(x_n**2) + coeff_out[1]*(x_n**3))
                 
        whole_length += np.sqrt((y_n - y)**2 +dx**2  )
        y = y_n
        x = x_n
    
    length = 0
    x = 0
    y = 0
    while True:
        x_n = x + dx
        y_n = (coeff_out[0]*(x_n**2) + coeff_out[1]*(x_n**3))
        length += np.sqrt((y_n - y)**2 +dx**2  )
        y = y_n
        x = x_n
        if length > whole_length/2 >0:
            return whole_length , length , [x, y] 


 
def poly_plot(coeff_out, t):
    return coeff_out[0]*(t**2)+coeff_out[1]*(t**3)


def residual(coeff_out,line_x_coord,line_y_coord ):
    return coeff_out[0]*line_x_coord**2 + coeff_out[1]*line_x_coord**3 -line_y_coord







middle_to_bound = [(rotated_to_point_moved[0][0] + rotated_line[-1][0])/2 , (rotated_to_point_moved[0][1] + rotated_line[-1][1])/2 ]
middle_to_bound_e = [(rotated_line[-2][0] + rotated_line[-1][0])/2 , (rotated_line[-2][1] + rotated_line[-1][1])/2 ]

a = 0
b= ((rotated_to_point_moved[0][1] + rotated_line[-1][1])/2 -  (rotated_line[-2][1] + rotated_line[-1][1])/2)/( (rotated_to_point_moved[0][0] + rotated_line[-1][0])/2 - (rotated_line[-2][0] + rotated_line[-1][0])/2  )               



# b =  ((rotated_to_point_moved[0][1] + rotated_aft_to_point_moved[0][1])/2 -  (rotated_line[-2][1] + rotated_line[-3][1])/2)/( (rotated_to_point_moved[0][0] + rotated_aft_to_point_moved[0][0])/2 - (rotated_line[-2][0] + rotated_line[-3][0])/2  )               
print("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",b)


whole_length , length , maxpoint  = curve_length(line_x_coord, poly(line_x_coord, line_y_coord, to_slope = b))

# whole_length , length , maxpoint  = curve_length([0, x_last], poly([x_last], [y_last], to_slope = b))
print(whole_length, length)
print( "res= ", residual(poly(line_x_coord, line_y_coord, to_slope = b),line_x_coord,line_y_coord ))

print( "res= ", residual( poly([x_last], [y_last], to_slope = b),line_x_coord,line_y_coord ))

# for 
#     if i = 0:
#         rotated_from_point_moved


#     whole_length , length , maxpoint  = curve_length(line_x_coord,poly(line_x_coord, line_y_coord, to_slope = b))
#     fig, ax = plt.subplots()

#     ax.plot(line_x_coord, line_y_coord, 'o')
#     ax.plot(maxpoint[0],maxpoint[1], 'o')
#     length =line_x_coord[-1]
#     tnew_new = np.linspace(0, length, num=100, endpoint=True)
#     ax.plot(line_x_coord, line_y_coord, 'o', tnew_new, poly_plot(poly(line_x_coord, line_y_coord, to_slope = b), tnew_new), '-')
#     ax.axis('equal')
#     plt.show()

plt.plot(maxpoint[0],maxpoint[1], 'o')
plt.plot(rotated_from_point_moved[0][0],rotated_from_point_moved[0][1], 'o')
plt.plot(rotated_to_point_moved[0][0],rotated_to_point_moved[0][1], 'o')
# ax.plot(((rotated_to_point_moved[0][1]  - rotated_line[-2][1])/2 +  rotated_line[-1][1]) ,((rotated_to_point_moved[0][0] - rotated_line[-2][0])/2 +  rotated_line[-1][0]), 'o' )
# b= ((rotated_to_point_moved[0][1]  - rotated_line[-2][1])/2 +  rotated_line[-1][1])/((rotated_to_point_moved[0][0] - rotated_line[-2][0])/2 +  rotated_line[-1][0])


length =x_last
tnew_new = np.linspace(0, length, num=100000, endpoint=True)
# plt.plot(line_x_coord, line_y_coord, 'o', tnew_new, poly_plot(poly([x_last], [y_last], to_slope = b), tnew_new), '-')

plt.plot(line_x_coord, line_y_coord, 'o', tnew_new, poly_plot(poly(line_x_coord, line_y_coord, to_slope = b), tnew_new), '-')
plt.plot(maxpoint[0],maxpoint[1], 'o')
plt.show()



#plt.plot([x_k, x_t],[y_k,y_t], 'o' )
# fig, ax = plt.subplots()

# ax.plot(line_x_coord, line_y_coord, 'o')
# ax.plot(maxpoint[0],maxpoint[1], 'o')
# ax.plot(rotated_from_point_moved[0][0],rotated_from_point_moved[0][1], 'o')
# ax.plot(rotated_to_point_moved[0][0],rotated_to_point_moved[0][1], 'o')
# # ax.plot(((rotated_to_point_moved[0][1]  - rotated_line[-2][1])/2 +  rotated_line[-1][1]) ,((rotated_to_point_moved[0][0] - rotated_line[-2][0])/2 +  rotated_line[-1][0]), 'o' )
# # b= ((rotated_to_point_moved[0][1]  - rotated_line[-2][1])/2 +  rotated_line[-1][1])/((rotated_to_point_moved[0][0] - rotated_line[-2][0])/2 +  rotated_line[-1][0])
# length =line_x_coord[-1]
# tnew_new = np.linspace(0, length, num=100, endpoint=True)
# ax.plot(line_x_coord, line_y_coord, 'o', tnew_new, poly_plot(poly([x_last], [y_last], to_slope = b), tnew_new), '-')
# ax.axis('equal')
# plt.show()

# plt.plot(line_x_coord, line_y_coord, 'o')
# plt.plot(maxpoint[0],maxpoint[1], 'o')
# length =line_x_coord[-1]
# tnew_new = np.linspace(0, length, num=100, endpoint=True)
# plt.plot(line_x_coord, line_y_coord, 'o', tnew_new, poly_plot(poly(line_x_coord, line_y_coord, to_slope = b), tnew_new), '-')
# plt.show()
##############################################################################################################



# a=0
# a = 0
b= (rotated_to_point_moved[0][1] - rotated_line[-2][1])/(rotated_to_point_moved[0][0] - rotated_line[-2][0])
b= ((rotated_to_point_moved[0][1] + rotated_line[-1][1])/2 -  (rotated_line[-2][1] + rotated_line[-1][1])/2)/( (rotated_to_point_moved[0][0] + rotated_line[-1][0])/2 - (rotated_line[-2][0] + rotated_line[-1][0])/2  )               

# b =  ((rotated_to_point_moved[0][1] + rotated_aft_to_point_moved[0][1])/2 -  (rotated_line[-2][1] + rotated_line[-3][1])/2)/( (rotated_to_point_moved[0][0] + rotated_aft_to_point_moved[0][0])/2 - (rotated_line[-2][0] + rotated_line[-3][0])/2  )               



print(b)
x_t =  (8*(maxpoint[1])  + rotated_line[-1][0]*(a+3*b) - 4*rotated_line[-1][1])/(3*(b-a))   # (1/2)*rotated_line[-1][0]  + x_k -2*maxpoint[0]
x_k = (8*maxpoint[0] -3*x_t -  rotated_line[-1][0])/3
y_k = a*x_k
y_t = b*(x_t- rotated_line[-1][0])+ rotated_line[-1][1]
print(x_t, x_k , y_k, y_t,rotated_line[-1][0], rotated_line[-1][1] )
print(maxpoint)

# x_t =  (8*(maxpoint[1])  + x_last*(3*b) - 4*y_last)/(3*b)   # (1/2)*rotated_line[-1][0]  + x_k -2*maxpoint[0]
# x_k = (8*maxpoint[0] -3*x_t -  x_last)/3
# y_k = 0
# y_t = b*(x_t- x_last)+ y_last

print(x_t, x_k , y_k, y_t,x_last, y_last)
print("dslkfdalsdkfnalskdnl")



# plt.plot([x_k, x_t],[y_k,y_t], 'o' )
plt.plot(line_x_coord, line_y_coord, 'o')
plt.plot(maxpoint[0],maxpoint[1], 'o')
plt.plot(rotated_from_point_moved[0][0],rotated_from_point_moved[0][1], 'o')
plt.plot(rotated_to_point_moved[0][0],rotated_to_point_moved[0][1], 'o')
# plt.plot(line_x_coord, line_y_coord, 'o', tnew_new, poly_plot(poly([x_last], [y_last], to_slope = b), tnew_new), '-')



length = 1
tnew = np.linspace(0, length, num=10000, endpoint=True)

def x_bezier(x_coord, t , length):
    return ((length-t)**3)*x_coord[0]/(length**3) + 3*t*((length-t)**2)*x_coord[1]/(length**3) + 3*(t**2)*(length-t)*x_coord[2]/(length**3) + (t**3)*x_coord[3]/(length**3)

def y_bezier(y_coord, t , length):
    return ((length-t)**3)*y_coord[0]/(length**3) + 3*t*((length-t)**2)*y_coord[1]/(length**3) + 3*(t**2)*(length-t)*y_coord[2]/(length**3) + (t**3)*y_coord[3]/(length**3)


import scipy.special
print("binomial coeff " ,scipy.special.binom(2, 1) )
print("binomial coeff " ,scipy.special.binom(2, 2) )
print("binomial coeff " ,scipy.special.binom(2, 0) )

def x_bezier_ex(x_coord,t ):
    coeff = [scipy.special.binom(len(x_coord)-1, i) for i in range(len(x_coord)-1) ]
    coeff.append(1)
    coeff = np.array(coeff)
    # t = np.array([  t**i   for i  in range( len(x_coord)-1 ) ])
    
    # tr = np.array([  (1-t)**i   for i  in range( len(x_coord)-1 ) ])
    
    # bezier =t*tr
    # return bezier
    # poly = []
    
    # for i in range(len(x_coord)):
        
    #     coeff =np.array([scipy.special.binom(len(x_coord), i) for k in range(len(x_coord)) ])
    #     xco = np.array([x_coord[i] for k in range(len(x_coord)) ])
        
    #     poly += xco*((t)**i)*((1-t)**(len(x_coord)-i))*coeff
        
        
    #     xc =  x_coord[i]
    #     tt = ((1-t)**(len(x_coord)-i))
    #     ttt=  (t)**i
    return x_coord[0]*((1-t)**7)*coeff[0] + x_coord[1]*((t)**1)*((1-t)**6)*coeff[1]+ x_coord[2]*((t)**2)*((1-t)**5)*coeff[2]+ x_coord[3]*((t)**3)*((1-t)**4)*coeff[3]+ x_coord[4]*((t)**4)*((1-t)**3)*coeff[4]+ x_coord[5]*((t)**5)*((1-t)**2)*coeff[5]+ x_coord[6]*(t**6)*(1-t)*coeff[6]+ x_coord[7]*(t**7)
    
def x_bezier_ex(x_coord,t ):
    coeff = [scipy.special.binom(len(x_coord)-1, i) for i in range(len(x_coord)-1) ]
    coeff.append(1)
    coeff = np.array(coeff)
    # t = np.array([  t**i   for i  in range( len(x_coord)-1 ) ])
    
    # tr = np.array([  (1-t)**i   for i  in range( len(x_coord)-1 ) ])
    
    # bezier =t*tr
    # return bezier
    # poly = []
    
    # for i in range(len(x_coord)):
        
    #     coeff =np.array([scipy.special.binom(len(x_coord), i) for k in range(len(x_coord)) ])
    #     xco = np.array([x_coord[i] for k in range(len(x_coord)) ])
        
    #     poly += xco*((t)**i)*((1-t)**(len(x_coord)-i))*coeff
        
        
    #     xc =  x_coord[i]
    #     tt = ((1-t)**(len(x_coord)-i))
    #     ttt=  (t)**i
    return x_coord[0]*((1-t)**7)*coeff[0] + x_coord[1]*((t)**1)*((1-t)**6)*coeff[1]+ x_coord[2]*((t)**2)*((1-t)**5)*coeff[2]+ x_coord[3]*((t)**3)*((1-t)**4)*coeff[3]+ x_coord[4]*((t)**4)*((1-t)**3)*coeff[4]+ x_coord[5]*((t)**5)*((1-t)**2)*coeff[5]+ x_coord[6]*(t**6)*(1-t)*coeff[6]+ x_coord[7]*(t**7)
    
# plt.plot(line_x_coord, line_y_coord, 'o', x_bezier([0,x_k,x_t,rotated_line[-1][0] ], tnew, length),  y_bezier([0, y_k,y_t, rotated_line[-1][1]], tnew, length), '-')

plt.plot( x_bezier([0,x_k,x_t,rotated_line[-1][0] ], tnew, length),  y_bezier([0, y_k,y_t, rotated_line[-1][1]], tnew, length), '-')
plt.show()

plt.plot(line_x_coord, line_y_coord, 'o')

# plt.plot( x_bezier(line_x_coord, tnew,1),  x_bezier(line_y_coord, tnew,1), '-')
plt.plot( x_bezier_ex(line_x_coord, tnew),  x_bezier_ex(line_y_coord, tnew), '-')
plt.plot(rotated_from_point_moved[0][0],rotated_from_point_moved[0][1], 'o')
plt.plot(rotated_to_point_moved[0][0],rotated_to_point_moved[0][1], 'o')
# print("xxxxxxxxxxxxxxxxxxxxxxxxxx",x_bezier_ex(line_x_coord, tnew))
plt.show()




# #####################################boundary condition ###########################

# sinecurve = np.array(sinecurve)
# lane_vector = sinecurve[:,0:2]

# plt.plot(lane_vector[:,0], lane_vector[:,1], 'o')
# plt.plot(from_point[0], from_point[1], 'o')
# # plt.plot(rotated_from_point_moved[0][0],rotated_from_point_moved[0][1],'o')


# # plt.plot(road_aft_to_point[0],road_aft_to_point[1],'o')
# # plt.plot(road_pre_from_point[0],road_pre_from_point[1],'o')
# plt.plot(to_point[0],to_point[1],'o')
# plt.show()


# x_init = lane_vector[0][0]
# y_init = lane_vector[0][1]
# print(x_init, y_init,"init, pre")
# x_init = (lane_vector[0][0] +lane_vector[1][0]  + from_point[0])/3
# y_init = (lane_vector[0][1] +lane_vector[1][1]  + from_point[1])/3
# print(x_init, y_init,"init")




# init_coord = np.array([x_init, y_init])
# line_moved_origin = lane_vector - init_coord

# from_point_moved = from_point - init_coord
# to_point_moved =  to_point - init_coord 

# # aft_to_point_moved = road_aft_to_point - init_coord
# # pre_from_point_moved = road_pre_from_point - init_coord



# from_u =  line_moved_origin[1][0] - from_point_moved[0]
# from_v = line_moved_origin[1][1]  - from_point_moved[1]

# from_u =  (line_moved_origin[1][0] + line_moved_origin[0][0])/2 - (from_point_moved[0] +  line_moved_origin[0][0])/2
# from_v = (line_moved_origin[1][1] + line_moved_origin[0][1])/2  - (from_point_moved[1] +  line_moved_origin[0][1])/2

# from_u = (line_moved_origin[2][0] + line_moved_origin[1][0])/2 - (from_point_moved[0] +  pre_from_point_moved[0])/2
# from_v =  (line_moved_origin[2][1] + line_moved_origin[1][1])/2  - (from_point_moved[1] +  pre_from_point_moved[1])/2

# to_u = line_moved_origin[-2][0] - to_point_moved[0]
# to_v = line_moved_origin[-2][1]  - to_point_moved[1]


# from_heading = np.arctan2(from_v, from_u) 
# to_heading = np.arctan2(to_v, to_u)  
# from_inv_heading = (-1) * from_heading

# rotated_aft_to_point_moved = coordinate_transform(from_inv_heading, [aft_to_point_moved])

# rotated_pre_from_point_moved = coordinate_transform(from_inv_heading, [pre_from_point_moved])

# rotated_line = coordinate_transform(from_inv_heading, line_moved_origin)
# rotated_from_point_moved = coordinate_transform(from_inv_heading, [from_point_moved])
# rotated_to_point_moved = coordinate_transform(from_inv_heading, [to_point_moved])

# x_last  = (rotated_to_point_moved[0][0] + rotated_line[-1][0] + rotated_line[-2][0])/3
# y_last = (rotated_to_point_moved[0][1] + rotated_line[-1][1] + rotated_line[-2][1])/3
# print(x_last, y_last ,"last")
# print("rotated_from_point_moved",rotated_from_point_moved,"rotated_to_point_moved",rotated_to_point_moved)

# line_x_coord = rotated_line[:,0]
# line_y_coord = rotated_line[:,1]


# plt.plot(rotated_aft_to_point_moved[0][0], rotated_aft_to_point_moved[0][1], 'o')
# plt.plot(rotated_pre_from_point_moved[0][0], rotated_pre_from_point_moved[0][1], 'o')
# plt.plot(line_x_coord, line_y_coord, 'o')
# plt.plot(rotated_from_point_moved[0][0], rotated_from_point_moved[0][1], 'o')
# # plt.plot(rotated_from_point_moved[0][0],rotated_from_point_moved[0][1],'o')
# # plt.plot(rotated_line[])
# # plt.plot(x_init, y_init, "x")
# plt.plot(x_last, y_last, "x")
# middle_to_bound = [(rotated_to_point_moved[0][0] + rotated_line[-1][0])/2 , (rotated_to_point_moved[0][1] + rotated_line[-1][1])/2 ]
# middle_to_bound_e = [(rotated_line[-2][0] + rotated_line[-1][0])/2 , (rotated_line[-2][1] + rotated_line[-1][1])/2 ]
# # plt.plot(x_init, y_init, "o")
# plt.plot(middle_to_bound_e[0],middle_to_bound_e[1],'x')
# plt.plot(middle_to_bound[0],middle_to_bound[1],'x')
# plt.plot(rotated_to_point_moved[0][0],rotated_to_point_moved[0][1],'o')
# plt.show()



# min = whole_length(rotated_line)

# for i  in range(2, len(rotated_line)):
  
    
#     if till_length(rotated_line[:i])- whole_length(rotated_line)/2 >0 :
#         rate_a = np.abs(till_length(rotated_line[:i-1])- whole_length(rotated_line)/2)
#         rate_b = np.abs(till_length(rotated_line[:i-2])- whole_length(rotated_line)/2)
#         print("rate",rate_a, rate_b)
#         maxpoint =  [(rotated_line[i-1][0]*rate_a + rotated_line[i-2][0]*rate_b ) /(rate_a + rate_b) ,( rotated_line[i-1][1]*rate_a + rotated_line[i-2][1]*rate_b)  /(rate_a + rate_b) ]
#         middle_a = rotated_line[i-1]
#         middle_b = rotated_line[i-2]
#         break

#maxpoint= [(rotated_line[0][0]+rotated_line[-1][0])/2 , (rotated_line[0][1] + rotated_line[-1][1])/2]
# plt.plot(line_x_coord, line_y_coord, 'o')
# plt.plot(middle_a[0],middle_a[1],"o", middle_b[0],middle_b[1], "o")
# plt.plot(maxpoint[0],maxpoint[1], 'o')
# plt.show()
###############################################################################################################################

def poly(line_x_coord, line_y_coord, to_slope = 0):
    x = line_x_coord[-1]
    y = line_y_coord[-1]
    if to_slope ==0:
        to_slope = (line_y_coord[-1] - line_y_coord[-2]) / (line_x_coord[-1] - line_x_coord[-2])
    d =  ((to_slope- 2*(y/x))/(x**2) )
    c = y/(x**2) - d*x 
    coeff_out = np.array([c, d])
    
    return coeff_out

def curve_length(line_x_coord,coeff_out, half = True):
    x = 0
    y = 0 
    dx = line_x_coord[-1]/100000
    whole_length = 0
    for i  in range(100000):
        x_n = x + dx
        y_n = (coeff_out[0]*(x_n**2) + coeff_out[1]*(x_n**3))
                 
        whole_length += np.sqrt((y_n - y)**2 +dx**2  )
        y = y_n
        x = x_n
    
    length = 0
    x = 0
    y = 0
    while True:
        x_n = x + dx
        y_n = (coeff_out[0]*(x_n**2) + coeff_out[1]*(x_n**3))
        length += np.sqrt((y_n - y)**2 +dx**2  )
        y = y_n
        x = x_n
        if length > whole_length/2 >0:
            return whole_length , length , [x, y] 


 
def poly_plot(coeff_out, t):
    return coeff_out[0]*(t**2)+coeff_out[1]*(t**3)


def residual(coeff_out,line_x_coord,line_y_coord ):
    return coeff_out[0]*line_x_coord**2 + coeff_out[1]*line_x_coord**3 -line_y_coord







middle_to_bound = [(rotated_to_point_moved[0][0] + rotated_line[-1][0])/2 , (rotated_to_point_moved[0][1] + rotated_line[-1][1])/2 ]
middle_to_bound_e = [(rotated_line[-2][0] + rotated_line[-1][0])/2 , (rotated_line[-2][1] + rotated_line[-1][1])/2 ]

a = 0
b= ((rotated_to_point_moved[0][1] + rotated_line[-1][1])/2 -  (rotated_line[-2][1] + rotated_line[-1][1])/2)/( (rotated_to_point_moved[0][0] + rotated_line[-1][0])/2 - (rotated_line[-2][0] + rotated_line[-1][0])/2  )               



# b =  ((rotated_to_point_moved[0][1] + rotated_aft_to_point_moved[0][1])/2 -  (rotated_line[-2][1] + rotated_line[-3][1])/2)/( (rotated_to_point_moved[0][0] + rotated_aft_to_point_moved[0][0])/2 - (rotated_line[-2][0] + rotated_line[-3][0])/2  )               
print("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",b)


whole_length , length , maxpoint  = curve_length(line_x_coord, poly(line_x_coord, line_y_coord, to_slope = b))

# whole_length , length , maxpoint  = curve_length([0, x_last], poly([x_last], [y_last], to_slope = b))
print(whole_length, length)
print( "res= ", residual(poly(line_x_coord, line_y_coord, to_slope = b),line_x_coord,line_y_coord ))

print( "res= ", residual( poly([x_last], [y_last], to_slope = b),line_x_coord,line_y_coord ))

# for 
#     if i = 0:
#         rotated_from_point_moved


#     whole_length , length , maxpoint  = curve_length(line_x_coord,poly(line_x_coord, line_y_coord, to_slope = b))
#     fig, ax = plt.subplots()

#     ax.plot(line_x_coord, line_y_coord, 'o')
#     ax.plot(maxpoint[0],maxpoint[1], 'o')
#     length =line_x_coord[-1]
#     tnew_new = np.linspace(0, length, num=100, endpoint=True)
#     ax.plot(line_x_coord, line_y_coord, 'o', tnew_new, poly_plot(poly(line_x_coord, line_y_coord, to_slope = b), tnew_new), '-')
#     ax.axis('equal')
#     plt.show()

plt.plot(maxpoint[0],maxpoint[1], 'o')
plt.plot(rotated_from_point_moved[0][0],rotated_from_point_moved[0][1], 'o')
plt.plot(rotated_to_point_moved[0][0],rotated_to_point_moved[0][1], 'o')
# ax.plot(((rotated_to_point_moved[0][1]  - rotated_line[-2][1])/2 +  rotated_line[-1][1]) ,((rotated_to_point_moved[0][0] - rotated_line[-2][0])/2 +  rotated_line[-1][0]), 'o' )
# b= ((rotated_to_point_moved[0][1]  - rotated_line[-2][1])/2 +  rotated_line[-1][1])/((rotated_to_point_moved[0][0] - rotated_line[-2][0])/2 +  rotated_line[-1][0])


length =x_last
tnew_new = np.linspace(0, length, num=100000, endpoint=True)
plt.plot(line_x_coord, line_y_coord, 'o', tnew_new, poly_plot(poly([x_last], [y_last], to_slope = b), tnew_new), '-')

# plt.plot(line_x_coord, line_y_coord, 'o', tnew_new, poly_plot(poly(line_x_coord, line_y_coord, to_slope = b), tnew_new), '-')
plt.plot(maxpoint[0],maxpoint[1], 'o')
plt.show()



#plt.plot([x_k, x_t],[y_k,y_t], 'o' )
# fig, ax = plt.subplots()

# ax.plot(line_x_coord, line_y_coord, 'o')
# ax.plot(maxpoint[0],maxpoint[1], 'o')
# ax.plot(rotated_from_point_moved[0][0],rotated_from_point_moved[0][1], 'o')
# ax.plot(rotated_to_point_moved[0][0],rotated_to_point_moved[0][1], 'o')
# # ax.plot(((rotated_to_point_moved[0][1]  - rotated_line[-2][1])/2 +  rotated_line[-1][1]) ,((rotated_to_point_moved[0][0] - rotated_line[-2][0])/2 +  rotated_line[-1][0]), 'o' )
# # b= ((rotated_to_point_moved[0][1]  - rotated_line[-2][1])/2 +  rotated_line[-1][1])/((rotated_to_point_moved[0][0] - rotated_line[-2][0])/2 +  rotated_line[-1][0])
# length =line_x_coord[-1]
# tnew_new = np.linspace(0, length, num=100, endpoint=True)
# ax.plot(line_x_coord, line_y_coord, 'o', tnew_new, poly_plot(poly([x_last], [y_last], to_slope = b), tnew_new), '-')
# ax.axis('equal')
# plt.show()

# plt.plot(line_x_coord, line_y_coord, 'o')
# plt.plot(maxpoint[0],maxpoint[1], 'o')
# length =line_x_coord[-1]
# tnew_new = np.linspace(0, length, num=100, endpoint=True)
# plt.plot(line_x_coord, line_y_coord, 'o', tnew_new, poly_plot(poly(line_x_coord, line_y_coord, to_slope = b), tnew_new), '-')
# plt.show()
##############################################################################################################



# a=0
# a = 0
b= (rotated_to_point_moved[0][1] - rotated_line[-2][1])/(rotated_to_point_moved[0][0] - rotated_line[-2][0])

# b =  ((rotated_to_point_moved[0][1] + rotated_aft_to_point_moved[0][1])/2 -  (rotated_line[-2][1] + rotated_line[-3][1])/2)/( (rotated_to_point_moved[0][0] + rotated_aft_to_point_moved[0][0])/2 - (rotated_line[-2][0] + rotated_line[-3][0])/2  )               



print(b)
x_t =  (8*(maxpoint[1])  + rotated_line[-1][0]*(a+3*b) - 4*rotated_line[-1][1])/(3*(b-a))   # (1/2)*rotated_line[-1][0]  + x_k -2*maxpoint[0]
x_k = (8*maxpoint[0] -3*x_t -  rotated_line[-1][0])/3
y_k = a*x_k
y_t = b*(x_t- rotated_line[-1][0])+ rotated_line[-1][1]
print(x_t, x_k , y_k, y_t,rotated_line[-1][0], rotated_line[-1][1] )
print(maxpoint)

# x_t =  (8*(maxpoint[1])  + x_last*(3*b) - 4*y_last)/(3*b)   # (1/2)*rotated_line[-1][0]  + x_k -2*maxpoint[0]
# x_k = (8*maxpoint[0] -3*x_t -  x_last)/3
# y_k = 0
# y_t = b*(x_t- x_last)+ y_last

print(x_t, x_k , y_k, y_t,x_last, y_last)
print("dslkfdalsdkfnalskdnl")



# plt.plot([x_k, x_t],[y_k,y_t], 'o' )
plt.plot(line_x_coord, line_y_coord, 'o')
plt.plot(maxpoint[0],maxpoint[1], 'o')
plt.plot(rotated_from_point_moved[0][0],rotated_from_point_moved[0][1], 'o')
plt.plot(rotated_to_point_moved[0][0],rotated_to_point_moved[0][1], 'o')
plt.plot(line_x_coord, line_y_coord, 'o', tnew_new, poly_plot(poly([x_last], [y_last], to_slope = b), tnew_new), '-')



length = 1
tnew = np.linspace(0, length, num=100000, endpoint=True)

def x_bezier(x_coord, t , length):
    return ((length-t)**3)*x_coord[0]/(length**3) + 3*t*((length-t)**2)*x_coord[1]/(length**3) + 3*(t**2)*(length-t)*x_coord[2]/(length**3) + (t**3)*x_coord[3]/(length**3)

def y_bezier(y_coord, t , length):
    return ((length-t)**3)*y_coord[0]/(length**3) + 3*t*((length-t)**2)*y_coord[1]/(length**3) + 3*(t**2)*(length-t)*y_coord[2]/(length**3) + (t**3)*y_coord[3]/(length**3)


# plt.plot(line_x_coord, line_y_coord, 'o', x_bezier([0,x_k,x_t,rotated_line[-1][0] ], tnew, length),  y_bezier([0, y_k,y_t, rotated_line[-1][1]], tnew, length), '-')

plt.plot( x_bezier([0,x_k,x_t,x_last ], tnew, length),  y_bezier([0, y_k,y_t, y_last], tnew, length), '-')

plt.show()




















######################################################## 첫 끝 중간지점의 가장 가까운 포인트
def length(last_point,  point):
    b = np.sqrt(last_point[0]**2+ last_point[1]**2)
    a = abs(last_point[1]*point[0] - last_point[0]*point[1])
    return a/b
# middlepoint = [ (rotated_line[0][0]+rotated_line[-1][0]) /2,  (rotated_line[0][1]+rotated_line[-1][1]) /2 ]

# maxpoint = sorted(rotated_line ,reverse = True, key= lambda x: length(middlepoint,x))[0]



def whole_length(data_set):
    length = 0
    for j in range(1, len(data_set)):
        length +=np.sqrt( (data_set[j][0] -data_set[j-1][0])**2 +(data_set[j][1] -data_set[j-1][1])**2)
    
    #print(length)
    return length




def till_length(data):
    till_length = 0 
    for j  in range(1, len(data)):
        till_length +=np.sqrt((data[j][0] -data[j-1][0])**2 +(data[j][1] -data[j-1][1])**2)
        #print("till_length ",till_length)
    return till_length
# min =whole_length(rotated_line)
# for i  in range(2, len(rotated_line)):
     
#     if  np.abs(till_length(rotated_line[:i])- whole_length(rotated_line)/2) <min:
#         print("min", min , np.abs(till_length(rotated_line[:i])- whole_length(rotated_line)/2) )
#         min = np.abs(till_length(rotated_line[:i])- whole_length(rotated_line)/2)
#         print("min?????????",i,min, rotated_line[i])
#         maxpoint = rotated_line[i]


# print(maxpoint)




# a=rotated_line[1][1]/rotated_line[1][0]
# b= (rotated_line[-1][1] - rotated_line[-2][1])/(rotated_line[-1][0] - rotated_line[-2][0])



# x_t =  (8*(maxpoint[1]- a*maxpoint[0])  + rotated_line[-1][0]*(a+3*b) - 4*rotated_line[-1][1])/(3*(b-a))   # (1/2)*rotated_line[-1][0]  + x_k -2*maxpoint[0]
# x_k = (8*maxpoint[0] -3*x_t -  rotated_line[-1][0])/3


# y_k = a*x_k
# y_t = b*(x_t- rotated_line[-1][0])+ rotated_line[-1][1]
# print(x_k, x_t)
# print(y_k, y_t)


# plt.plot([x_k, x_t],[y_k,y_t], 'o' )
# plt.plot(line_x_coord, line_y_coord, 'o')
# plt.plot(maxpoint[0],maxpoint[1], 'o')
# plt.show()

def get_linearity(x, y, angle):
    """
    Determines all vectors within a line are aligned within [angle] degrees

    Arguments:
    x: list of all vector x coordinates
    y: list of all vector y coordinates
    angle: the minimum angle allowed to be considered linear [degrees]
    """
    x = x - x[0]
    y = y - y[0]
    min_angle = np.deg2rad(angle)  # determines linearity condition
    for i in range(len(x) - 1):
        cross_prod_2d = x[i]*y[i+1] - x[i+1]*y[i]
        cross_mag = np.sqrt(cross_prod_2d**2)
        mag = np.sqrt((x[i]**2 + y[i]**2) * (x[i+1]**2 + y[i+1]**2))
        threshold = np.sin(min_angle) * mag
        if cross_mag > threshold:
            return False
    return True










# lane_vector = lane_vector[:,0:2]
        
# x_init = lane_vector[0][0]
# y_init = lane_vector[0][1]
        
# init_coord = np.array([x_init, y_init])
# line_moved_origin = lane_vector - init_coord
# from_point = from_point[:2]
# to_point = to_point[:2]
# from_point_moved = from_point - init_coord
# to_point_moved =  to_point - init_coord 

# from_u =  line_moved_origin[1][0] - from_point_moved[0]
# from_v = line_moved_origin[1][1]  - from_point_moved[1]

# from_heading = np.arctan2(from_v, from_u) 
# from_inv_heading = (-1) * from_heading
        
# rotated_line = coordinate_transform(from_inv_heading, line_moved_origin)
# rotated_to_point_moved = coordinate_transform(from_inv_heading, [to_point_moved])
        

# line_x_coord = rotated_line[:,0]
# line_y_coord = rotated_line[:,1]
        

# if  len(rotated_line)%2==0:
#     maxpoint = [(line_x_coord[len(rotated_line)//2 -1] +  line_x_coord[len(rotated_line)//2])/2 ,(line_y_coord[len(rotated_line)//2-1] +  line_y_coord[len(rotated_line)//2])/2] 
# else:
#     maxpoint = [line_x_coord[len(rotated_line)//2]  , line_y_coord[len(rotated_line)//2]] 

            
# a= 0
# b= (rotated_to_point_moved[0][1] - rotated_line[-2][1])/(rotated_to_point_moved[0][0] - rotated_line[-2][0])

# x_t =  (8*(maxpoint[1]- a*maxpoint[0])  + rotated_line[-1][0]*(a+3*b) - 4*rotated_line[-1][1])/(3*(b-a))  
# x_k = (8*maxpoint[0] -3*x_t -  rotated_line[-1][0])/3
# y_k = a*x_k
# y_t = b*(x_t- rotated_line[-1][0])+ rotated_line[-1][1]
        
# line_x_coord =   [line_x_coord[0], x_k, x_t , line_x_coord[-1]] 
# line_y_coord =   [line_y_coord[0], y_k, y_t , line_y_coord[-1]] 

# dU = line_x_coord[3] -3*line_x_coord[2] +3*line_x_coord[1]
# cU = 3*line_x_coord[2]-6*line_x_coord[1]
# bU = 3*line_x_coord[1]
            
# dV = line_y_coord[3]-3*line_y_coord[2]
# cV = 3*line_y_coord[2]

# poly_out = [0, bU, cU ,dU, 0, 0, cV, dV ]





line_x_coord = [  0.        ,  62.89774635, 177.19833103, 245.4789619 ,296.1190183 ]
line_y_coord = [ 0.        ,  0.07110701, -0.12308331, -0.15935658, -0.09497471]


maxpoint = [177.19833102727472, -0.12308331461273525]

rotated_to_point_moved = [[ 3.57100610e+02, -1.11346516e-01]]
rotated_line =[[ 0.00000000e+00,  0.00000000e+00],
       [ 6.28977464e+01,  7.11070089e-02],
       [ 1.77198331e+02, -1.23083315e-01],
       [ 2.45478962e+02, -1.59356581e-01],
       [ 2.96119018e+02, -9.49747146e-02]]


a= 0
b= (rotated_to_point_moved[0][1] - rotated_line[-2][1])/(rotated_to_point_moved[0][0] - rotated_line[-2][0])
print("bbbbbbbbbbbb", b )
b = 0.00043011427689482315

x_t =  (8*(maxpoint[1]- a*maxpoint[0])  + rotated_line[-1][0]*(a+3*b) - 4*rotated_line[-1][1])/(3*(b-a))  
x_k = (8*maxpoint[0] -3*x_t -  rotated_line[-1][0])/3
y_k = a*x_k
y_t = b*(x_t- rotated_line[-1][0])+ rotated_line[-1][1]
        
line_x_coord =   [line_x_coord[0], x_k, x_t , line_x_coord[-1]] 
line_y_coord =   [line_y_coord[0], y_k, y_t , line_y_coord[-1]] 

line_x_coord = [  0.        ,  62.89774635, 177.19833103, 245.4789619 ,296.1190183 ]
line_y_coord = [ 0.        ,  0.07110701, -0.12308331, -0.15935658, -0.09497471]

length = 1
def x_bezier(x_coord, t , length):
    return ((length-t)**3)*x_coord[0]/(length**3) + 3*t*((length-t)**2)*x_coord[1]/(length**3) + 3*(t**2)*(length-t)*x_coord[2]/(length**3) + (t**3)*x_coord[3]/(length**3)

def y_bezier(y_coord, t , length):
    return ((length-t)**3)*y_coord[0]/(length**3) + 3*t*((length-t)**2)*y_coord[1]/(length**3) + 3*(t**2)*(length-t)*y_coord[2]/(length**3) + (t**3)*y_coord[3]/(length**3)


# plt.plot( maxpoint[0],maxpoint[1],"o",line_x_coord, line_y_coord, 'o', x_bezier([0,x_k,x_t,rotated_line[-1][0] ], tnew, length),  y_bezier([0, y_k,y_t, rotated_line[-1][1]], tnew, length), '-')

# plt.show()

print(np.abs(line_y_coord))

def get_linearity(x_list, y_list,thr):
        
        if max(np.abs(y_list))/x_list[-1] < 0.001:
            return True
        else:
            return False
print("linearity", get_linearity(line_x_coord,line_y_coord,0.1 ))


##########################elevation for 4 point #############################################################################

# elevation_data = [[-333.7340849000029, -391.4253868581727, 0.3318573405991394], 
#  [-291.12466569792014, -399.88966717990115, 0.4117097886998593],
#   [-264.6900869582314, -405.2813925300725, 0.44413811029425787], 
#   [-251.4933183285175, -408.02970198960975, 0.49770908915932566],
#    [-231.5162501297891, -412.4602708895691, 0.5630140213799493]]
# ele3 = [[-1431.6962722662138, -168.79844506038353, 6.101223428314491], [-1428.9940582902636, -173.85324581107125, 6.325570409006154], [-1425.9993010148173, -179.16788848489523, 6.564446467165265], [-1422.6305619742488, -184.8229530272074, 6.8351206164250655], [-1419.9373393534916, -189.12972566764802, 7.053817431160869], [-1416.3528817343758, -194.59349595569074, 7.311942000511294], [-1412.86104894022, -199.68823893973604, 7.557937081562557], [-1408.3440199439647, -205.9637220343575, 7.8143231663932085], [-1405.2347190688597, -210.0832881773822, 7.960255570296468], [-1402.0623309233924, -214.13799002580345, 8.098750973942874], [-1397.842574881739, -219.26534230960533, 8.256308144892518], [-1394.4645765973255, -223.15349943609908, 8.364324703178625], [-1390.2770028960658, -227.76348936744034, 8.472042247222998], [-1386.0003710859455, -232.26038444601, 8.544642937828389], [-1382.4015722257318, -235.91138144768775, 8.594889547787794], [-1377.6587800601264, -240.5230988287367, 8.633646330225236], [-1373.9186715872493, -244.02991771139205, 8.65380087367679], [-1368.1841566090006, -249.16463245404884, 8.667037146801402], [-1362.3286366600078, -254.1538203326054, 
# 8.640015108159695], [-1350.5826704673236, -263.67775384290144, 8.487329751237283], [-1345.2582745973486, -267.7455151122995, 8.406401652149789], [-1341.135078502004, -270.7381273326464, 8.327068522951148], [-1334.1912978163455, -275.3943642252125, 8.1779806105734], [-1328.1297259508865, -279.10033161053434, 8.0175704832868], [-1323.6707399744773, -281.65809901431203, 7.88379475014758], [-1313.5576093784766, -287.0669872746803, 7.59213761793605], [-1305.6176027572947, -290.998091944959, 7.392015478975882], [-1301.0882110425737, -293.10918222367764, 7.279749339839093], [-1296.5726262313547, -295.13303187536076, 7.169544577838529], [-1291.1007186498027, -297.44734682142735, 7.05184868284444], [-1282.2380555070704, -300.9011579202488, 6.862001633673003], [-1273.2723847897723, -304.0456729326397, 6.635870961837394], [-1265.4031258873874, -306.5332391122356, 6.426337570155681], [-1257.7139513556613, -308.71189243206754, 6.222269203335877], [-1248.2538405531086, -311.07249900279567, 5.981132262948066], [-1238.7220572551014, -313.11497211037204, 5.7468959942860565], [-1230.7202029911568, -314.589797552675, 5.524009587784821], [-1222.2461090260185, -315.8690369683318, 5.28890706754639], [-1217.352661380428, -316.4746446600184, 5.138002503835704], [-1209.3844496679958, -317.2525487206876, 
# 4.835910199588486], [-1197.7993631641148, -318.0425108433701, 4.399562312998235], [-1184.5923653602367, -318.60132045904174, 3.888217602853846], [-1166.397384392796, -319.1494366824627, 3.210626336979985], [-1123.5366391938878, -320.6535071944818, 1.7150406304391588], [-1110.4952536668861, -321.4579441486858, 1.3855986370587487], [-1097.410752870841, -322.5723819071427, 1.1476945270548544], [-1087.5432153748116, -323.6843891479075, 0.9920835698466934], [-1079.171956740669, -324.7774218544364, 0.871392145154557], [-1071.0745815237751, -325.9699051952921, 0.8220272743669295], [-1062.99841724406, -327.31022203480825, 0.7998604109912861], [-1051.5585563172353, -329.53252448374406, 0.7587802717815961], [-1019.2142489190446, -336.2792970999144, 0.6133701838371657]]

# def elevation(elevation_data):
#     lane_vector = np.array(elevation_data)
#     lane_vector_xy = lane_vector[:,0:2]
        
#     # transform initial point to origin
#     global_x_init = lane_vector_xy[0][0]
#     global_y_init = lane_vector_xy[0][1]
#     init_coord = np.array([global_x_init, global_y_init])
#     line_moved_origin = lane_vector_xy - init_coord

#     line_x_coord = line_moved_origin[:,0]
#     line_y_coord = line_moved_origin[:,1]

#     line_s_coord = np.sqrt(np.power(line_x_coord,2)
#         + np.power(line_y_coord, 2))
#     line_h_coord = lane_vector[:,2]


    
#     line_s_coord_temp = []
#     line_h_coord_temp = []
#     for i in range(len(lane_vector)//4):
        
#         line_s_coord_temp.append(line_s_coord[4*i:4*i+4])
#         line_h_coord_temp.append(line_h_coord[4*i:4*i+4])
#     return line_s_coord_temp , line_h_coord_temp


# def cubicgraph(h_coord , t):
#     return h_coord[0] + h_coord[1]*t +h_coord[2]*(t**2)+  h_coord[3]*(t**3) 

# s,h = elevation(ele3)
# for i in range(len(s)):
#     if len(s[i]) == 1:
#         break
#     if len(s[i]) ==2 or len(s[i]) ==3:
#         b = (h[i][-1]-h[i][0])/(s[i][-1]-s[i][0])
#         a = -s[i][0]*b + h[i][0]
#         poly_out = np.array([a, b, 0, 0])
        
#         tnew = np.linspace(s[i][0], s[i][-1], num=10, endpoint=True)
#         #plt.plot(0, h[i], 'o',tnew, cubicgraph(poly_out, tnew))
#         #plt.show()
    
    
#     length = s[i][-1]
#     a = h[i][0]
#     b = (3*h[i][1] - 3*h[i][0])/(length**1)
#     c = (3*h[i][-2] - 6*h[i][1] + 3*h[i][0])/(length**2)
#     d = (h[i][-1] -3*h[i][-2] +3*h[i][1] -h[i][0])/(length**3)
#     poly_out = np.array([a, b, c, d])
#     tnew = np.linspace(s[i][0], s[i][-1], num=10, endpoint=True)
    
#     print( cubicgraph(poly_out, tnew)[0] , h[i][0])
    
#     #plt.plot(s[i], h[i], 'o',tnew, cubicgraph(poly_out, tnew))
    
#     #plt.show()

# #control_point  = [line_h_coord[0],line_h_coord[1], line_h_coord[-2], line_h_coord[-1]] 

# def controlpoint_bezier(x_coord, t , length):
#     return ((length-t)**3)*x_coord[0]/(length**3) + 3*t*((length-t)**2)*x_coord[1]/(length**3) + 3*(t**2)*(length-t)*x_coord[2]/(length**3) + (t**3)*x_coord[3]/(length**3)
    
# def cubicgraph(h_coord , t):
#     return h_coord[0] + h_coord[1]*t +h_coord[2]*(t**2)+  h_coord[3]*(t**3) 


#tnew = np.linspace(0, line_s_coord[-1], num=100, endpoint=True)

#plt.plot(line_s_coord, line_h_coord, 'o', tnew, controlpoint_bezier(control_point, tnew, line_s_coord[-1]), '-')


#plt.plot(line_s_coord, line_h_coord, 'o',tnew, cubicgraph(poly_out, tnew))




# ele1 =  [[-1424.3339539781446, -160.46145346574485, 5.498070004770096],
#  [-1431.4512791235466, -146.38046640902758, 5.099242434360171],
#   [-1442.8459381295834, -123.87021113466471, 4.83070413773455]]
# ele2 = [[-1435.7663780290168, -154.35987806413323, 5.630742322611042],
#  [-1430.9554250511574, -163.77576368767768, 5.946468540774152]]


# # elevation(ele3)
# # plt.show()

# k= 24
# lane_vector = np.array(ele3[k:k+4])
# lane_vector_xy = lane_vector[:,0:2]
        
#     # transform initial point to origin
# global_x_init = lane_vector_xy[0][0]
# global_y_init = lane_vector_xy[0][1]
# init_coord = np.array([global_x_init, global_y_init])
# line_moved_origin = lane_vector_xy - init_coord

# line_x_coord = line_moved_origin[:,0]
# line_y_coord = line_moved_origin[:,1]

# line_s_coord = np.sqrt(np.power(line_x_coord,2)
#     + np.power(line_y_coord, 2))
# line_h_coord = lane_vector[:,2]


# print(line_s_coord,line_h_coord)
# if len(lane_vector) ==2 or len(lane_vector) ==3:
#     b = (line_h_coord[-1]-line_h_coord[0])/(line_s_coord[-1]-line_s_coord[0])
#     a = -line_s_coord[0]*b + line_h_coord[0]
        
        
#     poly_out = np.array([a, b, 0, 0])
         
        
# length = line_s_coord[-1]
# a = line_h_coord[0]
# b = (3*line_h_coord[1] - 3*line_h_coord[0])/(length**1)
# c = (3*line_h_coord[-2] - 6*line_h_coord[1] + 3*line_h_coord[0])/(length**2)
# d = (line_h_coord[-1] -3*line_h_coord[-2] +3*line_h_coord[1] -line_h_coord[0])/(length**3)
# poly_out = np.array([a, b, c, d])
        
# print(poly_out)
# tnew = np.linspace(0, line_s_coord[-1], num=100, endpoint=True)
# plt.plot(line_s_coord, line_h_coord, 'o',tnew, cubicgraph(poly_out, tnew))

# plt.show()


#########################################################################################################

# length = 1
# tnew = np.linspace(0, length, num=100, endpoint=True)

# def x_bezier(x_coord, t , length):
#     return ((length-t)**3)*x_coord[0]/(length**3) + 3*t*((length-t)**2)*x_coord[1]/(length**3) + 3*(t**2)*(length-t)*x_coord[2]/(length**3) + (t**3)*x_coord[3]/(length**3)

# def y_bezier(y_coord, t , length):
#     return ((length-t)**3)*y_coord[0]/(length**3) + 3*t*((length-t)**2)*y_coord[1]/(length**3) + 3*(t**2)*(length-t)*y_coord[2]/(length**3) + (t**3)*y_coord[3]/(length**3)



# plt.plot(line_x_coord, line_y_coord, 'o', x_bezier([0,x_k,x_t,rotated_line[-1][0] ], tnew, length),  y_bezier([0, y_k,y_t, rotated_line[-1][1]], tnew, length), '-')

# plt.show()























# coef = [0,1.2167380567292597e+01,4.7885294970164648e+02,-4.2274019003777840e+02,0,0,0,-1.3610207543779259e+02]

# def cubicx(coef, t):
#     coef =coef 

#     return coef[3]*t**3+ coef[2]*t**2+ coef[1]*t+ coef[0]

# def cubicy(coef, t):
#     coef =coef 

#     return coef[-1]*t**3+ coef[-2]*t**2+ coef[-3]*t+ coef[-4]


# x_coord3 = x_coord[-1] - ( y_coord[-1]/(y_coord[-1] - y_coord[-2])*(x_coord[-1]-x_coord[-2] )    )

# line_x_coord_new =   [x_coord[0], x_coord[1], x_coord3 , x_coord[-1]] 
# line_y_coord_new =   [y_coord[0],0, 0 , y_coord[-1]] 

# print(line_x_coord)

# plt.plot(line_x_coord, line_y_coord, 'o',cubicx(coef,  tnew),  cubicy(coef,  tnew),  'r','-')
# plt.figure(figsize=(6, 4))




# x_coord3 = x_coord[-1] - ( y_coord[-1]/(y_coord[-1] - y_coord[-2])*(line_x_coord[-1]-line_x_coord[-2] )    )

# line_x_coord_new =   [line_x_coord[0], line_x_coord[1], x_coord3 , line_x_coord[-1]] 
# line_y_coord_new =   [line_y_coord[0],0, 0 , line_y_coord[-1]] 


# plt.plot(line_x_coord, line_y_coord, 'o', coeff_x_bezier(line_x_coord_new, length,  tnew),  coeff_y_bezier(line_y_coord_new, length, tnew), '-')

# plt.title("all point ")
# plt.show()


# plt.show()









""" 
#########################################














x_coor = [ 0.         , 5.64313586 ,17.22662278, 27]
y_coor = [0.     ,    0.       ,  0.22857455, 0.6]
line_x_coord= x_coor
line_y_coord= y_coor




#plt.plot(x_coor, y_coor, 'o', coeff_x_bezier(par_coef_x, tnew),  coeff_y_bezier(par_coef_y, tnew), '-')

#plt.show()
##########################################################


#print( x_bezier(x_coord, tnew, length),  y_bezier(y_coord, tnew, length))

plt.plot(x_coordthr, y_coordthr, 'o', x_bezier(x_coordthr, tnew, length),  y_bezier(y_coordthr, tnew, length), '-')

plt.show()

plt.plot(x_coord, y_coord, 'o', x_bezier(x_coord, tnew, length),  y_bezier(y_coord, tnew, length), '-')

plt.show()


def cubic(coef, x):
    coef =coef 

    return coef[0]*x**3+ coef[1]*x**2+ coef[0]*x+ coef[0]




print(x_coor[-1]/y_coor[-1]) 

plt.plot(x_coor, y_coor, 'o', xnew, cubic(coef,xnew), '-')
plt.legend(['data', 'numpypoly', 'scipy'], loc='best')
plt.show()

"""






















"""

x_coordk = [0, 5, 10, 15, 21, 30, 37 ]
y_coordk = [0, 0, 0.05, 0.1, 0.12, 0.15, 0.18]




def x_bezierk(x_coordk, t , length):
    return ( (length-t)**6)*x_coordk[0]+ 6*(t**1)*((length-t)**5)*x_coordk[1]+ 15*(t**2)*((length-t)**4)*x_coordk[2]+ 20*(t**3)*((length-t)**3)*x_coordk[3]+ 15*(t**4)*((length-t)**2)*x_coordk[4]+ 3*(t**5)*((length-t)**1)*x_coordk[5]+ (t**6)*x_coordk[6]

def y_bezierk(y_coordk, t , length):
    return ((length-t)**6)*y_coordk[0]+ 6*(t**1)*((length-t)**5)*y_coordk[1]+ 15*(t**2)*((length-t)**4)*y_coordk[2]+ 20*(t**3)*((length-t)**3)*y_coordk[3]+ 15*(t**4)*((length-t)**2)*y_coordk[4]+ 3*(t**5)*((length-t)**1)*y_coordk[5]+ (t**6)*y_coordk[6]

plt.plot(x_coordk, y_coordk, 'o', x_bezierk(x_coordk, tnew, length),  y_bezierk(y_coordk, tnew, length), '-')

plt.show()

x_coordkk = [0, 5, 10, 15, 21, 30, 37 ]
y_coordkk = [0, 0, 0.03, 0.08, 0.15, 0.16, 0.18]

plt.plot(x_coordkk, y_coordkk, 'o', x_bezierk(x_coordkk, tnew, length),  y_bezierk(y_coordkk, tnew, length), '-')

plt.show()
"""

# try:
#                     road_from_point = ref_line_mark.get_from_links()[0].points[-2]
#                 except:
#                     road_from_point = ref_line_mark.points[0]
#                 try:
#                     road_to_point =  ref_line_mark.get_to_links()[0].points[1]
#                 except:
#                     road_to_point =  ref_line_mark.points[-1]
# if len(vector_list) ==1:
#                         from_point = road_from_point
#                         to_point = road_to_point
#                     else:

#                         if i == 0:
#                             from_point = road_from_point
#                             to_point = vector_list[i+1][1]
                        
#                         elif i == len(vector_list)-1:
#                             to_point = road_to_point
#                             from_point = vector_list[i-1][-2]
                        
#                         else:
#                             from_point = vector_list[i-1][-2]
#                             to_point = vector_list[i+1][1]
# init_coord, heading, arclength, poly_geo, uv_point = \
#                         self.bezier_geometry_general_boundary_all(vector, to_point, from_point)

# def till_length(self, data):
#         till_length = 0 
#         for j  in range(1, len(data)):
#             till_length +=np.sqrt((data[j][0] -data[j-1][0])**2 +(data[j][1] -data[j-1][1])**2)
#         return till_length
    
#     def bezier_geometry_general_boundary_all(self, lane_vector, to_point, from_point):
#         lane_vector = lane_vector[:,0:2]
        
#         x_init = lane_vector[0][0]
#         y_init = lane_vector[0][1]
        
#         init_coord = np.array([x_init, y_init])
#         line_moved_origin = lane_vector - init_coord
#         from_point = from_point[:2]
#         to_point = to_point[:2]
#         from_point_moved = from_point - init_coord
#         to_point_moved =  to_point - init_coord 

#         from_u =  line_moved_origin[1][0] - from_point_moved[0]
#         from_v = line_moved_origin[1][1]  - from_point_moved[1]

#         from_heading = np.arctan2(from_v, from_u) 
#         from_inv_heading = (-1) * from_heading

#         rotated_line = self.coordinate_transform(from_inv_heading, line_moved_origin)
#         rotated_to_point_moved = self.coordinate_transform(from_inv_heading, [to_point_moved])
        
#         arc = self.arclength_of_line(line_moved_origin[:,0], line_moved_origin[:,1])
#         arclength = arc + 0.1  # forced connections b/n roads
    
#         line_x_coord = rotated_line[:,0]
#         line_y_coord = rotated_line[:,1]
        
#         def poly(line_x_coord, line_y_coord, to_slope = 0):
#             x = line_x_coord[-1]
#             y = line_y_coord[-1]
#             if to_slope ==0:
#                 to_slope = (line_y_coord[-1] - line_y_coord[-2]) / (line_x_coord[-1] - line_x_coord[-2])
#             d =  ((to_slope- 2*(y/x))/(x**2) )
#             c = y/(x**2) - d*x 
#             coeff_out = np.array([c, d])
    
#             return coeff_out

#         def curve_length(line_x_coord,coeff_out, half = True):
#             x = 0
#             y = 0 
#             dx = line_x_coord[-1]/1000
#             whole_length = 0
#             for i  in range(1000):
#                 x_n = x + dx
#                 y_n = (coeff_out[0]*(x_n**2) + coeff_out[1]*(x_n**3))
                 
#                 whole_length += np.sqrt((y_n - y)**2 +dx**2  )
#                 y = y_n
#                 x = x_n
    
#             length = 0
#             x = 0
#             y = 0
#             while True:
#                 x_n = x + dx
#                 y_n = (coeff_out[0]*(x_n**2) + coeff_out[1]*(x_n**3))
#                 length += np.sqrt((y_n - y)**2 +dx**2  )
#                 y = y_n
#                 x = x_n
#                 if length > whole_length/2 >0:
#                     return whole_length , length , [x, y] 

           
#         a= 0
#         b= (rotated_to_point_moved[0][1] - rotated_line[-2][1])/(rotated_to_point_moved[0][0] - rotated_line[-2][0])
        
#         whole_length , length , maxpoint  = curve_length(line_x_coord,poly(line_x_coord, line_y_coord, to_slope = b))
        
#         arclength = whole_length
        
#         if max(line_x_coord)> line_x_coord[-1]:
#             def whole_length(data_set):
#                 length = 0
#                 for j in range(1, len(data_set)):
#                     length +=np.sqrt( (data_set[j][0] -data_set[j-1][0])**2 +(data_set[j][1] -data_set[j-1][1])**2)
    
#                 return length

#             def till_length(data):
#                 till_length = 0 
#                 for j  in range(1, len(data)):
#                     till_length +=np.sqrt((data[j][0] -data[j-1][0])**2 +(data[j][1] -data[j-1][1])**2)
#                 return till_length
            
#             min =whole_length(rotated_line)
            
#             for i  in range(2, len(rotated_line)):
#                 if  np.abs(till_length(rotated_line[:i])- whole_length(rotated_line)/2) <min:
#                     min = np.abs(till_length(rotated_line[:i])- whole_length(rotated_line)/2)
#                     maxpoint = rotated_line[i]


#         x_t =  (8*(maxpoint[1]- a*maxpoint[0])  + rotated_line[-1][0]*(a+3*b) - 4*rotated_line[-1][1])/(3*(b-a))  
#         x_k = (8*maxpoint[0] -3*x_t -  rotated_line[-1][0])/3
#         y_k = a*x_k
#         y_t = b*(x_t- rotated_line[-1][0])+ rotated_line[-1][1]
        
#         line_x_coord =   [line_x_coord[0], x_k, x_t , line_x_coord[-1]] 
#         line_y_coord =   [line_y_coord[0], y_k, y_t , line_y_coord[-1]] 

#         dU = line_x_coord[3] -3*line_x_coord[2] +3*line_x_coord[1]
#         cU = 3*line_x_coord[2]-6*line_x_coord[1]
#         bU = 3*line_x_coord[1]
            
#         dV = line_y_coord[3]-3*line_y_coord[2]
#         cV = 3*line_y_coord[2]

#         poly_out = [0, bU, cU ,dU, 0, 0, cV, dV ]
        
#         return init_coord, from_heading, arclength, poly_out, rotated_line
