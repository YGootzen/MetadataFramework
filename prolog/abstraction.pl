{\rtf1\ansi\ansicpg1252\cocoartf2709
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 % Implementation of the second abstraction layer, accompanying the paper:\
% "A Metadata-based Framework for Combining Data Sources in Official Statistics"\
\
% Each node (a1, a2, b1, ...) represents a data source from the first abstraction layer.\
% An edge (makes(b2, a3), makes(b3, a4), ...) exists if a manipulation is valid between two (or three) data sources.\
% The data sources available are denoted by start_have().\
% To experiment with only a part of the data sources available, comment out start_have() using "%".\
% \
% The idea behind this implementation is to see every edge as an AND-edge. The edges that only require one dataset as\
% input can be seen as a combination of that dataset and an emptyset. The emptyset contains no information. \
\
%%% example %%%\
% see example_abstraction.pdf\
% define case\
\
start_have(a1).\
start_have(a2).\
start_have(a3).\
start_have(a4).\
start_have(a5).\
\
% define edges (placeholder for aggregation and conversion)\
makes(b2, a3).\
makes(b3, a4).\
makes(a4, b3).\
makes(a5, b2).\
makes(b4, a5).\
makes(b1, b2).\
makes(b2, c1).\
makes(c1, b2).\
makes(c1, b3).\
makes(b2, c2).\
makes(c3, b4).\
makes(c2, d1).\
makes(c3, d1).\
makes(d2, c3).\
\
% AND-edges\
makes(a1, a2, b1).\
makes(b3, b4, c2).\
makes(d1, d2, e1).\
\
\
\
% first we need a graph that will check whether the starting point of a path is a have(),\
% needed because usually, for a regular graph, all edges and nodes are true\
% avoid this whole thing by creating one origin node. All have(x) will be converted into a\
% makes(origin, x). as to make it into an edge, just like a regular graph\
makes(A, emptyset, B) :- makes(A, B).  % to avoid having to write emptyset all the time\
makes(origin, origin, X) :- start_have(X).  % in edge-form\
\
help_have(emptyset).  % always required\
\
\
% the emptyset does not have a connection to the origin\
have(X) :-\
        start_have(X);\
        help_have(X).\
\
% now, instead of asking whether we can make a single data source x, we can\
% ask whether there are two distinct paths from origin to x.\
\
% ensure that make is symmetrical:\
makes_sym(A, B, C) :- makes(A, B, C); makes(B, A, C).\
\
% if we have X then we do not even have to create it\
create(X) :-\
        have(X).\
\
% if X is the result of a single edge, use an emptyset to construct it\
create(X) :-\
        %nl, format('?? create empty ~w', [X]),\
        makes_sym(Y, emptyset, X),  % this is an AND-edge with Y and an emptyset\
        travel(origin, Y, [origin, X], _),  % ensure there is at least one non-cyclic path to the origin that does not include X\
        create(Y),\
        !,  % take first path (otherwise cycles will be returned for bidirectional single edges)\
        nl, format('~w -> ~w',[Y, X]).\
\
% for a true AND-edge\
create(X) :-\
    	makes(A, B, X),  % A and B make X\
    	%nl, format('???? create ~w + ~w -> ~w ?', [A, B, X]),\
    	A \\== B,  % A and B are different\
    	%nl, format('     create ~w + _ -> ~w ?', [A, X]),\
    	travel(origin, A, [origin, X], _),  % ensure there is at least one non-cyclic path to the origin that does not include X\
        create(A),\
        !,   % only one correct path needed for this branch\
        %format('  YES'),\
        %nl, format('     create _ + ~w -> ~w ?', [B, X]),\
        travel(origin, B, [origin, X], _),  % ensure there is at least one non-cyclic path to the origin that does not include X\
        create(B),\
    	%format('  YES'),\
        !,  % for now, we are happy with a single correct path\
    	nl, format('~w + ~w -> ~w',[A, B, X]).\
\
path_partial(A,B,Path) :-\
       %nl, format('path partial ~w -> ~w ?', [A, B]),\
       travel(A,B,[A],Q),\
       reverse(Q,Path).\
travel(A,B,P,[B|P]) :-\
       %nl, format('travel ~w -> ~w ?', [A, B]),\
       makes_sym(A,_,B).\
travel(A,B,Visited,Path) :-\
       %nl, format('travel ~w -> ~w , visited ~w?', [A, B, Visited]),\
       makes_sym(A,_,C),\
       C \\== B,\
       \\+member(C,Visited),\
       travel(C,B,[C|Visited],Path).%,\
       %format('  YES').\
}
