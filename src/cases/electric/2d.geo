h=0.1;

Point(1) = {0,0,0,h};
Point(2) = {1,0,0,h};
Point(3) = {0,1,0,h};
Point(4) = {1,1,0,h};

Line(1) = {1,2};
Line(2) = {2,4};
Line(3) = {4,3};
Line(4) = {3,1};

Line Loop(1) = {1,2,3,4};
Plane Surface(1) = {1};

Physical Surface("omega") = {1};
Physical Line("gamma") = {1,2,3,4};
