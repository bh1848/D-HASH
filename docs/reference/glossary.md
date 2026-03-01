# Glossary

Primary (P_k)
    The node selected by consistent hashing.

Alternate (A_k)
    Deterministically selected successor node.

T
    Hot-key promotion threshold.

W
    Window size for routing alternation.

delta
    read_count - T

Epoch
    floor(delta / W)
