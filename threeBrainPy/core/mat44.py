import numpy as np
import json

class Mat44(object):
    def __init__(self, mat = None, byrow = True, space_from = 'ras', space_to = 'ras', modality_from = "T1", modality_to = "T1"):
        '''
        Creates a 4x4 matrix.
        @param mat: The matrix, can be a 1D array of length 12 or 16, or a 2D array of shape (3,4) or (4,4).
        @param byrow: Whether the matrix is in row-major order (default) or column-major order.
        @param space_from: The space from which the matrix is defined, choices are "ras", "voxel", "ras_tkr", "mni305", "mni152".
            * "ras": scanner-RAS space
            * "voxel": voxel indexing space (or IJK space)
            * "ras_tkr": FreeSurfer RAS space, this is the space used internally by the viewer engine in JavaScript
            * "mni305": MNI305 template space
            * "mni152": MNI152 template space
            threeBrainPy does not limit the choices, but the viewer only supports these spaces.
        @param space_to: The space to which the matrix is defined, choices are the same as `space_from`.
        @param modality_from: The imaging modality from which the matrix is defined, choices are "T1" or "CT" other modalities may be 
            added in the future, default is "T1".
        @param modality_to: The imaging modality to which the matrix is defined. If set to `None`, then it will be set
            with the same value as `modality_from` automatically; default choice is `None`.
        '''
        if mat is None:
            self.mat = np.eye(4)
        else:
            mat = np.array(mat, copy = True, dtype=float)
            if mat.size == 12:
                if byrow:
                    mat = mat.reshape(3,4)
                else:
                    mat = mat.reshape(4,3).transpose()
                map = np.append(mat, [[0,0,0,1]], axis=0)
            else:
                map = mat.reshape(4, 4)
                if not byrow:
                    mat = mat.transpose()
            self.mat = map
        self.space_from = space_from
        self.space_to = space_to
        self.modality_from = modality_from
        self.modality_to = modality_from if modality_to is None else modality_to
        self.extra = {}

    def __mul__(self, other):
        if isinstance(other, Mat44):
            # modalities must match
            if self.modality_from != other.modality_to:
                raise ValueError(f"Mat44 multiply: modalities must match, but got {self.modality_from} and {other.modality_to}")
            # spaces must match
            if self.space_from != other.space_to:
                raise ValueError(f"Mat44 multiply: spaces must match, but got {self.space_from} and {other.space_to}")
        return Mat44(np.matmul(self.mat, other.mat), modality_from=other.modality_from, modality_to=self.modality_to, space_from=other.space_from, space_to=self.space_to)

    def __repr__(self):
        re = repr(self.mat)
        return f"Mat44 ({self.modality_from}.{self.space_from} -> {self.modality_to}.{self.space_to}): \n{ re }"

    def __str__(self):
        return str(self.mat)

    def __getitem__(self, key):
        return self.mat[key]

    def __setitem__(self, key, value):
        self.mat[key] = value

    def __eq__(self, other):
        return np.allclose(self.mat, other.mat)

    def __ne__(self, other):
        return not np.allclose(self.mat, other.mat)

    def __hash__(self):
        return hash(str(self.mat))

    def __copy__(self):
        return Mat44(self.mat.copy(), space_from = self.space_from, space_to = self.space_to, modality_from = self.modality_from, modality_to = self.modality_to)

    def __deepcopy__(self, memo):
        return Mat44(self.mat.copy(), space_from = self.space_from, space_to = self.space_to, modality_from = self.modality_from, modality_to = self.modality_to)

    def __iter__(self):
        return iter(self.mat)

    def __len__(self):
        return len(self.mat)

    def __abs__(self):
        return abs(self.mat)

    def __neg__(self):
        return Mat44(-self.mat, space_from = self.space_from, space_to = self.space_to, modality_from = self.modality_from, modality_to = self.modality_to)

    def __pos__(self):
        return Mat44(+self.mat, space_from = self.space_from, space_to = self.space_to, modality_from = self.modality_from, modality_to = self.modality_to)

    def __add__(self, other):
        if isinstance(other, Mat44):
            # modalities must match
            if self.modality_from != other.modality_from:
                raise ValueError(f"Mat44 add: modality_from must match, but got {self.modality_from} and {other.modality_from}")
            if self.modality_to != other.modality_to:
                raise ValueError(f"Mat44 add: modality_from must match, but got {self.modality_to} and {other.modality_to}")
            # spaces must match
            if self.space_from != other.space_from:
                raise ValueError(f"Mat44 add: space_from must match, but got {self.space_from} and {other.space_from}")
            if self.space_to != other.space_to:
                raise ValueError(f"Mat44 add: space_to must match, but got {self.space_to} and {other.space_to}")
        return Mat44(self.mat + other.mat, space_from = self.space_from, space_to = self.space_to, modality_from = self.modality_from, modality_to = self.modality_to)

    def __sub__(self, other):
        if isinstance(other, Mat44):
            # modalities must match
            if self.modality_from != other.modality_from:
                raise ValueError(f"Mat44 add: modality_from must match, but got {self.modality_from} and {other.modality_from}")
            if self.modality_to != other.modality_to:
                raise ValueError(f"Mat44 add: modality_from must match, but got {self.modality_to} and {other.modality_to}")
            # spaces must match
            if self.space_from != other.space_from:
                raise ValueError(f"Mat44 add: space_from must match, but got {self.space_from} and {other.space_from}")
            if self.space_to != other.space_to:
                raise ValueError(f"Mat44 add: space_to must match, but got {self.space_to} and {other.space_to}")
        return Mat44(self.mat - other.mat, space_from = self.space_from, space_to = self.space_to, modality_from = self.modality_from, modality_to = self.modality_to)

    def __floordiv__(self, other):
        if isinstance(other, Mat44):
            # modalities must match
            if self.modality_from != other.modality_from:
                raise ValueError(f"Mat44 add: modality_from must match, but got {self.modality_from} and {other.modality_from}")
            if self.modality_to != other.modality_to:
                raise ValueError(f"Mat44 add: modality_from must match, but got {self.modality_to} and {other.modality_to}")
            # spaces must match
            if self.space_from != other.space_from:
                raise ValueError(f"Mat44 add: space_from must match, but got {self.space_from} and {other.space_from}")
            if self.space_to != other.space_to:
                raise ValueError(f"Mat44 add: space_to must match, but got {self.space_to} and {other.space_to}")
        return Mat44(self.mat // other.mat, space_from = self.space_from, space_to = self.space_to, modality_from = self.modality_from, modality_to = self.modality_to)

    def __mod__(self, other):
        if isinstance(other, Mat44):
            # modalities must match
            if self.modality_from != other.modality_from:
                raise ValueError(f"Mat44 add: modality_from must match, but got {self.modality_from} and {other.modality_from}")
            if self.modality_to != other.modality_to:
                raise ValueError(f"Mat44 add: modality_from must match, but got {self.modality_to} and {other.modality_to}")
            # spaces must match
            if self.space_from != other.space_from:
                raise ValueError(f"Mat44 add: space_from must match, but got {self.space_from} and {other.space_from}")
            if self.space_to != other.space_to:
                raise ValueError(f"Mat44 add: space_to must match, but got {self.space_to} and {other.space_to}")
        return Mat44(self.mat % other.mat, space_from = self.space_from, space_to = self.space_to, modality_from = self.modality_from, modality_to = self.modality_to)

    def __pow__(self, other):
        if isinstance(other, Mat44):
            # modalities must match
            if self.modality_from != other.modality_from:
                raise ValueError(f"Mat44 add: modality_from must match, but got {self.modality_from} and {other.modality_from}")
            if self.modality_to != other.modality_to:
                raise ValueError(f"Mat44 add: modality_from must match, but got {self.modality_to} and {other.modality_to}")
            # spaces must match
            if self.space_from != other.space_from:
                raise ValueError(f"Mat44 add: space_from must match, but got {self.space_from} and {other.space_from}")
            if self.space_to != other.space_to:
                raise ValueError(f"Mat44 add: space_to must match, but got {self.space_to} and {other.space_to}")
        return Mat44(self.mat ** other.mat, space_from = self.space_from, space_to = self.space_to, modality_from = self.modality_from, modality_to = self.modality_to)

    def __invert__(self):
        return Mat44(np.linalg.inv(self.mat), space_from = self.space_to, space_to = self.space_from, modality_from = self.modality_to, modality_to = self.modality_from)
    
    def to_json(self, **kwargs):
        return json.dumps(np.ndarray.flatten(self.mat).tolist(), **kwargs)
    
# mat = Mat44([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])