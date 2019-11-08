# Addresses
11 p
11,12 p
$ p
/regex-without-flags/ p
/regex-with-flags/IM p
// p

# Bang to invert addresses
$ ! p

# Commands with no arguments
=
b
d
D
F
g
G
h
H
l
L
n
N
p
P
q
Q
t
T
x
z

# Commands with numeric argument
q 1
Q 22
l 333
L 4444

# Commands with labels
: label
b label_b
t label_t
T label_T

# Command v (label-like)
v 4.2

# Commands with files
r file_r
R file_R
w file_w
W file_W

# Commands with text
a text_a
i\
text_i
c\
text_c1 \
text_c2

# Command e (text-like)
e date

# Command y
y/abc/123/
y@abc@123@

# Command s
s///
s|||3
s/patt/repl/gipw filew

# Blocks
$ {
    p
}
