{\rtf1\ansi\ansicpg1252\cocoartf2709
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 % Implementation of the first abstraction layer, accompanying the paper:\
% "A Metadata-based Framework for Combining Data Sources in Official Statistics"\
\
% This implementation contains an attempt at path search through all combinations.\
% For short paths, this seems to work. For longer paths, the runtime on the available \
% equipment is so long that no conclusion has been made about whether or not the\
% implementaiton was succesfull.\
\
%%%%%%%%%%%%%%%%%%%%%%%%% facts %%%%%%%%%%%%%%%%%%%%%%%%%%%%%\
% variables\
variables_letters([c, r, m, od, p, t]).\
\
% variables granularity\
var_gran(c, [c0]).\
var_gran(r, [r0, r1]).\
var_gran(m, [m0]).\
var_gran(od, [od0]).\
var_gran(p, [p0]).\
var_gran(t, [t0, t1, t2]).\
\
% conversion facts\
% none in this case, but one initialisation is required, so we use "na"\
conversion_edge(na0, na1).\
\
% aggregation facts\
aggregates_edge(t0, t1).\
aggregates_edge(t1, t2).\
\
aggregates_edge(r0, r1).\
aggregates_edge(r1, r0).\
\
% available data sources\
start_have(data([c0], [r0, m0, t1])).  % RET counts\
start_have(data([p0], [od0, t2])).  % Admin\
start_have(data([m0, p0], [od0, t0])).  % ODiN\
start_have(data([r0], [r1, m0])).\
\
%%%%%%%%%%%%%%%%%%%%%%%%% general %%%%%%%%%%%%%%%%%%%%%%%%%%%%%\
% some general predicates used for reasoning with lists and sets\
\
% union of sets\
union_set(A, B, C) :-  % true if the union of sets A and B are equal to set C\
    union(A, B, X),\
    eq_set(X, C).\
\
% equality in sets\
% source: https://stackoverflow.com/questions/56718545/equality-of-sets\
eq_set(A, B) :-  % true if set A and set B contain the same elements\
    % prerequisites: A and B are lists without duplicates\
    sort(A, X), % read as "list A sorts into list S"\
    sort(B, X).\
\
% list without any double elements\
all_unique([]).  % based on https://stackoverflow.com/questions/37469017/prolog-how-to-limit-variable-list-length\
all_unique([E|Es]) :-\
   maplist(dif(E), Es),\
   all_unique(Es).\
\
% Is List the sorted version of itself? (for excluding permutations)\
is_sorted(List) :-\
    sort(List, SortedList),\
    List = SortedList.\
\
%%%%%%%%%%%%%%%%%%%%%%%%% aggregation %%%%%%%%%%%%%%%%%%%%%%%%%%\
% variable level\
% \
% aggregation is a directed uncyclic graph\
aggregates(X, Y) :- aggregates_path(X, Y, _).\
\
aggregates_path(X, Z, [])    :-  aggregates_edge(X, Z).\
aggregates_path(X, Z, [Y|T]) :-  aggregates_edge(X, Y), aggregates_path(Y, Z, T).\
\
% list level\
aggregates_list(HaveSet, WantedSet) :-\
    foreach(member(WantedVar, WantedSet), aggregates_list_var(HaveSet, WantedVar)).\
\
aggregates_list_var(HaveSet, WantedVar) :-\
    member(WantedVar, HaveSet);  % we already have this variable\
    aggregates(HaveVar, WantedVar),\
    member(HaveVar, HaveSet).\
\
%%%%%%%%%%%%%%%%%%%%%%%%% conversion %%%%%%%%%%%%%%%%%%%%%%%%%%\
% variable level\
\
% conversion is an undirected graph that may by cyclic\
% the cyclic behaviour can cause an infinite loop\
% to avoid this, we track the visited "nodes"\
\
converts(A, B) :- conversion_path(A, B, _).  % if any path exists, then conversion is possible\
\
conversion_connectedEdges(X,Y) :- conversion_edge(X,Y).\
conversion_connectedEdges(X,Y) :- conversion_edge(Y,X).\
\
conversion_path(A,B,Path) :-\
       conversion_travel(A,B,[A],Q),\
       reverse(Q,Path).\
\
conversion_travel(A,B,P,[B|P]) :-\
       conversion_connectedEdges(A,B).\
\
conversion_travel(A,B,Visited,Path) :-\
       conversion_connectedEdges(A,C),\
       C \\== B,  % C is not B, which we have already checked in previous part\
       \\+member(C,Visited),\
       conversion_travel(C,B,[C|Visited],Path).\
\
% list level\
% \
% converts: weither one variable can be converted into another variable\
% converts_list_var: weither one variable (WantedVar) can be converted from any variable in the list (HaveSet)\
% converts_list: weither the entire list of variables (WantedSet) can be converted from the other\
% list of variables (HaveSet)\
\
%for all VarWant in WantedSet there is a VarHave in HaveSet -> converts(var_have, var_want)\
converts_list(HaveSet, WantedSet) :-\
    foreach(member(WantedVar, WantedSet), converts_list_var(HaveSet, WantedVar)).\
\
converts_list_var(HaveSet, WantedVar) :-\
    member(WantedVar, HaveSet);  % we already have this variable\
    converts(HaveVar, WantedVar),\
    member(HaveVar, HaveSet).\
\
\
%%%%%%%%%%%%%%%%%%%%%%%%% combining %%%%%%%%%%%%%%%%%%%%%%%%%%\
% dataset 1 and 2 can be combined into dataset 3 if:\
% - R1, R2 and R3 are equal (set-wise, same order is not required)\
% - L3 is a subset of (or equal to) the union of L1 and L2\
\
combines_to(L1, R1, L2, R2, L3, R3) :-\
    R1=R2,\
    R2=R3,\
    variable_list_valid(_,L1),\
    variable_list_valid(_,L2),\
   union_set(L1, L2, L3).%,  % L3 subset of union of L1 and L2\
\
combines_to_loose(L1, R1, L2, R2, L3, R3) :-\
    R1=R2,\
    R2=R3,\
    variable_list_valid(_,L1),\
    variable_list_valid(_,L2),\
    subset(L3, X), \
	union_(L1, L2, X).%,  % L3 subset of union of L1 and L2\
\
\
%%%%%%%%%%%%%%%%%%%%%%%%% variable and data validity %%%%%%%%%%%%%%%%%%%%%%%%%\
%%% limit search to valid data sets and variables %%%\
\
% we can check whether a data set is valid by checking all variables\
% for being valid and checking that the variables are unique (to avoid\
% infinitely long lists)\
\
variable_valid(Letter, Granularity):-\
    variables_letters(V),  % look up all predefined variables\
    member(Letter, V),\
    var_gran(Letter, ValidGranularities),  % look up all valid granularities for this Letter\
    member(Granularity, ValidGranularities).\
\
variable_list_valid(ListLetters, ListGranularities) :-\
   variables_letters(V),  % look up all predefined variables\
   length(V, Vlength),\
   % conditions for ListLetters\
   length(HelpList1, Vlength),   % maximum wanted length\
   append(ListLetters, _, HelpList1),  % List\
   all_unique(ListLetters),\
   % limit length of ListGranularities\
   length(HelpList2, Vlength),\
   append(ListGranularities, _, HelpList2),\
   all_unique(ListGranularities),\
   % check that all variables are valid\
   maplist(variable_valid, ListLetters, ListGranularities),\
   % disqualify any permutations\
   is_sorted(ListLetters),\
   is_sorted(ListGranularities).\
\
data_valid(X_left, X_right) :-\
    variable_list_valid(_, X_left),  % X_left is valid\
    variable_list_valid(_, X_right).  % X_right is valid\
\
\
%%%%%%%%%%%%%%%%%%%%%%%%% explanation %%%%%%%%%%%%%%%%%%%%%%%%%\
% first we need a graph that will check whether the starting point of a path is a have(),\
% needed because usually, for a regular graph, all edges and nodes are true\
% avoid this whole thing by creating one origin node. All have(x) will be converted into a\
% makes(origin, x). as to make it into an edge, just like a regular graph\
\
%%%%%%%%%%%%%%%%%%%%%%%%% makes %%%%%%%%%%%%%%%%%%%%%%%%%\
%%% makes/2 %%%\
% single edges\
\
% any set we have at the start, is connected to the origin\
makes(origin, data(X_left, X_right)) :-\
    start_have(data(X_left, X_right)).  % in edge-form\
	% no valid check required because any start_have() data is assumed valid\
\
% aggregation or conversion (single edge):\
makes(data(A_left, A_right), data(B_left, B_right)) :-\
    data_valid(A_left, A_right),\
    A_right = B_right,  % no changes in the right side\
    data_valid(B_left, B_right),\
    converts_list(A_left, B_left),  % the left sides can be converted\
    !,\
    nl, format('   convert ~w -> ~w',[A_left, B_left]).\
\
makes(data(A_left, A_right), data(B_left, B_right)) :-\
    data_valid(A_left, A_right),\
    data_valid(B_left, B_right),\
    aggregates_list(A_right, B_right),  % the right sides can be aggregated\
    A_left = B_left,  % no changes in the left side\
    !,\
    nl, format('   aggregate ~w -> ~w',[A_right, B_right]).\
\
makes(data(A_left, A_right), data(B_left, B_right)) :-\
    data_valid(A_left, A_right),\
    data_valid(B_left, B_right),\
    converts_list(A_left, B_left),  % the left sides can be converted\
    aggregates_list(A_right, B_right),  % the right sides can be aggregated\
    !,\
    nl, format('   convert ~w -> ~w and aggregate ~w -> ~w' ,[A_left, B_left, A_right, B_right]).\
\
%%% makes/3 %%%\
% models first because they are specific\
%% RET case study model %%\
makes(data([p0, m0], [t1, od0]), data([p0], [t1, od0]), data([p0], [t1, od0, m0])) :-\
    nl, format('   model ([p0, m0], [t1, od0]) + ([p0], [t1, od0]) -> ([p0], [t1, od0, m0])').\
\
% AND-edges\
% any set we have at the start, is connected to the origin\
makes(origin, origin, data(X_left, X_right)) :-\
    start_have(data(X_left, X_right)),  % in edge-form\
    !,\
    nl, format('   start with data(~w, ~w)', [X_left, X_right]).\
	% no valid check needed because start_have() is assumed valid\
\
makes(data(A_left, A_right), data(B_left, B_right), data(C_left, C_right)) :-  % based on combining\
    data_valid(A_left, A_right),\
    data_valid(B_left, B_right),\
    data_valid(C_left, C_right),\
    combines_to(A_left, A_right, B_left, B_right, C_left, C_right),\
    !,\
    nl, format('   combine (~w, ~w) + (~w, ~w) -> (~w, ~w)',[A_left, A_right, B_left, B_right, C_left, C_right]).\
\
\
% convert makes/2 to makes/3 with the help of emptyset (necessary because travel/4 uses makes/3)\
makes(data(A_left, A_right), emptyset, data(C_left, C_right)) :-\
    makes(data(A_left, A_right), data(C_left, C_right)).\
\
makes(emptyset, data(A_left, A_right), data(C_left, C_right)) :-\
    makes(data(A_left, A_right), data(C_left, C_right)).\
\
%%%%%%%%%%%%%%%%%%%%%%%%% haves %%%%%%%%%%%%%%%%%%%%%%%%%\
%%% haves %%%\
help_have(emptyset).  % always required\
\
% the emptyset does not have a connection to the origin\
have(X) :-\
    start_have(X);\
    help_have(X).\
\
%%%%%%%%%%%%%%%%%%%%%%%%% create %%%%%%%%%%%%%%%%%%%%%%%%%\
%%% create %%%\
% there are multiple ways to create a data set\
\
% 1) if we have the data then we do not even have to create it\
create(data(X_left, X_right)) :-\
        have(data(X_left, X_right)),\
    	nl, format('   start with data(~w, ~w)', [X_left, X_right]),\
        !.  % no need to search further\
\
% 2) if X is the result of a single edge\
create(data(X_left, X_right)) :-\
    data_valid(Y_left, Y_right),\
    makes(data(Y_left, Y_right), data(X_left, X_right)),  % single edge\
    nl, format('* new attempt (single edge) *'),\
    travel(origin, data(Y_left, Y_right), [origin, data(X_left, X_right)], _),  % ensure there is at least one non-cyclic path to the origin that does not include X\
    create(data(Y_left, Y_right)),\
    !,  % take first path (otherwise cycles will be returned for bidirectional single edges)\
    nl, format(' SUCCES '),\
    nl, format('[~w, ~w] -> [~w, ~w]',[Y_left, Y_right, X_left, X_right]).\
\
\
% 3) if X is the result of an AND-edge\
create(data(X_left, X_right)) :-\
    makes(data(A_left, A_right), data(B_left, B_right), data(X_left, X_right)),  % A and B make X\
    A_left \\== B_left,  % A and B are different\
    A_right \\== B_right,  % A and B are different\
    nl, format('* new attempt (double edge) *'),\
    travel(origin, data(A_left, A_right), [origin, data(X_left, X_right)], _),  % ensure there is at least one non-cyclic path to the origin that does not include X\
    create(data(A_left, A_right)),\
    !,   % only one correct path needed for this branch\
    travel(origin, data(B_left, B_right), [origin, data(X_left, X_right)], _),  % ensure there is at least one non-cyclic path to the origin that does not include X\
    create(data(B_left, B_right)),\
    !,  % for now, we are satisfied with a single correct path\
    nl, format(' SUCCES '),\
    nl, format('[~w, ~w] + [~w, ~w] -> [~w, ~w]',[A_left, A_right, B_left, B_right, X_left, X_right]).\
\
%%%%%%%%%%%%%%%%%%%%%%%%% path search %%%%%%%%%%%%%%%%%%%%%%%%%\
% path search (for cyclic directed graph)\
path_partial(data(A_left, A_right), data(B_left, B_right), Path) :-\
       travel(data(A_left, A_right), data(B_left, B_right), [data(A_left, A_right)], Q),\
       reverse(Q, Path).\
\
travel(DA, DB, Path, [DB|Path]) :-\
       makes(DA, _, DB).\
\
travel(DA, DB, Visited, Path) :-\
       makes(DA, _, DC),\
       DB \\== DC,  % B and C are not the same\
       \\+member(DA, Visited),\
       travel(DC, DB,[DC|Visited], Path).\
\
\
\
\
}