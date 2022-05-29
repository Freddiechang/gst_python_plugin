"""
Reference: https://github.com/PhoebeWangintw/Feature-aware-texturing
"""
from skimage import measure
from scipy.sparse import csc_matrix
from scipy.optimize import curve_fit
from scipy.sparse.linalg import lsqr

import numpy as np
import matplotlib.pyplot as plt
import cv2
import math


class Mesh():
    def __init__(self, saliency_map, mask, target_size, quad_size, W):
        """
        saliency_map: 2D saliency map (h, w), with 1.5 x sigma
        mask: threshold mask for saliency (original_saliency > threshold)
        target_size: target image size (h, w)
        quad_size: size of the quad
        W: warping function
        """
        self.saliency_map = saliency_map
        self.quad_size = quad_size
        self.W = W
        self.target_size = target_size

        width = mask.shape[1] - 1
        height = mask.shape[0] - 1
        self.width = mask.shape[1]
        self.height = mask.shape[0]

        nq_col = math.ceil(width / self.quad_size)
        nq_row = math.ceil(height / self.quad_size)
        self.nq_col = nq_col
        self.nq_row = nq_row

        self.origin_vertices = []
        self.warped_vertices = []
        self.Q = []
        self.Q_label = []
        labels, max_num = measure.label(mask, background=0, return_num=True)
        self.labels = labels
        self.max_num = max_num
        is_mask = []
        group_id = []
        
        for y in self.__arange(height, quad_size):
            for x in self.__arange(width, quad_size):
                self.origin_vertices.append([y, x])
                is_mask.append(mask[y, x] != 0)
                group_id.append(labels[y, x])
       
        self.origin_vertices = np.array(self.origin_vertices).astype(np.float32)
        self.warped_vertices = self.origin_vertices.copy()
        self.warped_vertices = W(self.warped_vertices, 1)
        group_id = np.array(group_id)
        
        # quad
        self.Q_label = []
        idx = np.arange(len(self.origin_vertices)).reshape(self.nq_row+1, self.nq_col+1)
        for r in range(nq_row):
            for c in range(nq_col):
                vidx = [idx[r, c], idx[r, c+1], idx[r+1, c+1], idx[r+1, c]]
                self.Q.append(vidx)
                if any([is_mask[i] for i in vidx]):
                    self.Q_label.append(np.min(list(filter(lambda x: x > 0, [group_id[i] for i in vidx]))))
                else:
                    self.Q_label.append(0)

        self.Q = np.array(self.Q)
        self.Q_label = np.array(self.Q_label)
        
                
        # boundaries as hard constraints
        self.non_constraints_idx = idx[1:-1, :][:, 1:-1].flatten()
        self.idx_is_constraints = np.array([True] * (len(idx.flatten())))
        self.idx_is_constraints[self.non_constraints_idx] = False
        
        self.idx_to_ncidx = {}
        for i, idx in enumerate(self.non_constraints_idx):
            self.idx_to_ncidx[idx] = i
        
    
    def __arange(self, stop, step):
        """ helper function: same as np.arange but appends stop to the end """
        ret = np.arange(start=0, stop=stop, step=step)
        ret = np.append(ret, stop)
        return ret

    def init_r(self, n):
        """
        Initialize rigid transformation matrix
        """
        self.r = []
        for i in range(n):
            self.r.append(np.identity(2))   



    def compute_L2(self, w_f, saliency_map=None):
        """
        generate the left hand side matrix of the linear system (Ax = b)
        self: mesh
        w_f: default weight for non-salient areas
        saliency_map: saliency map
        centers: ndarray (n, 2), gaussian centers
        """
        rows = []
        cols = []
        data = []
        row_counts = 0
        d_max = np.sqrt(self.width ** 2 + self.height ** 2)
        
        for i, quad_idx in enumerate(self.Q):
            if self.Q_label[i]:
                if type(saliency_map) == np.ndarray:
                    v = np.zeros((4, 2))
                    for j in range(4):
                        v[j] = self.origin_vertices[quad_idx[j]]
                    lb = v.min(axis=0).astype(np.int)
                    ub = v.max(axis=0).astype(np.int)
                    w = np.mean(saliency_map[lb[0]:ub[0],lb[1]:ub[1]])
                else:
                    w = w_f
            else:
                w = 1
            
            for j in range(4):
                add_row = False
                k = quad_idx[j]
                k_plus1 = quad_idx[(j+1) % 4]
                
                if not self.idx_is_constraints[k]:
                    rows.append(row_counts)
                    cols.append(self.idx_to_ncidx[k])
                    data.append(-w)
                    add_row = True
                
                if not self.idx_is_constraints[k_plus1]:
                    rows.append(row_counts)
                    cols.append(self.idx_to_ncidx[k_plus1])
                    data.append(w)
                    add_row = True
                
                if add_row:
                    row_counts += 1
        for i in range(self.nq_row):
            if i == 0 or i == self.nq_row - 1:
                continue
            first = False
            for j in range(self.nq_col - 1):
                if j == 0 or j == self.nq_col - 2:
                    continue
                q = i * self.nq_col + j
                if (not first) and (not self.Q_label[q]):
                    q_first = q
                    first = True
                elif first and (not self.Q_label[q]):
                    if type(saliency_map) == np.ndarray:
                        v = np.zeros((4, 2))
                        for j in range(4):
                            v[j] = self.origin_vertices[quad_idx[j]]
                        lb = v.min(axis=0).astype(np.int)
                        ub = v.max(axis=0).astype(np.int)
                        w = np.mean(saliency_map[lb[0]:ub[0],lb[1]:ub[1]])
                    # if type(centers) == np.ndarray:
                    #     v = self.origin_vertices[self.idx_to_ncidx[self.Q[q][0]]].reshape(1, 2)
                    #     d = np.sqrt(np.sum((v - centers) ** 2, axis=1).min())
                    #     w = (d_max - d) / d_max * w_f
                    else:
                        w = 1
                    rows.append(row_counts)
                    cols.append(self.idx_to_ncidx[self.Q[q_first][0]])
                    data.append(w)
                    rows.append(row_counts)
                    cols.append(self.idx_to_ncidx[self.Q[q_first][1]])
                    data.append(-w)
                    rows.append(row_counts)
                    cols.append(self.idx_to_ncidx[self.Q[q][0]])
                    data.append(-w)
                    rows.append(row_counts)
                    cols.append(self.idx_to_ncidx[self.Q[q][1]])
                    data.append(w)
                    row_counts += 1
        for i in range(self.nq_col):
            if i == 0 or i == self.nq_col - 1:
                continue
            first = False
            for j in range(self.nq_row - 1):
                if j == 0 or j == self.nq_row - 2:
                    continue
                q = j * self.nq_col + i
                if (not first) and (not self.Q_label[q]):
                    q_first = q
                    first = True
                elif first and (not self.Q_label[q]):
                    if type(saliency_map) == np.ndarray:
                        v = np.zeros((4, 2))
                        for j in range(4):
                            v[j] = self.origin_vertices[quad_idx[j]]
                        lb = v.min(axis=0).astype(np.int)
                        ub = v.max(axis=0).astype(np.int)
                        w = np.mean(saliency_map[lb[0]:ub[0],lb[1]:ub[1]])
                    # if type(centers) == np.ndarray:
                    #     v = self.origin_vertices[self.idx_to_ncidx[self.Q[q][0]]].reshape(1, 2)
                    #     d = np.sqrt(np.sum((v - centers) ** 2, axis=1).min())
                    #     w = (d_max - d) / d_max * w_f
                    else:
                        w = 1
                    rows.append(row_counts)
                    cols.append(self.idx_to_ncidx[self.Q[q_first][3]])
                    data.append(w)
                    rows.append(row_counts)
                    cols.append(self.idx_to_ncidx[self.Q[q_first][0]])
                    data.append(-w)
                    rows.append(row_counts)
                    cols.append(self.idx_to_ncidx[self.Q[q][3]])
                    data.append(-w)
                    rows.append(row_counts)
                    cols.append(self.idx_to_ncidx[self.Q[q][0]])
                    data.append(w)
                    row_counts += 1      
        self.L = csc_matrix((data, (rows, cols)), shape=(row_counts, len(self.non_constraints_idx)))



    def compute_b2(self, w_f, saliency_map=None, scale=None):
        """
        generate the right hand side of the linear system (Ax = b)
        mesh: mesh
        w_f: default weight for non-salient areas
        r: rigid transformation matrices
        R: transformation function (takes coordinates and generates coordinates)
        V: vertex coordinates
        saliency_map: saliency map
        scale: ndarray (2,), scale restriction for height and width
        """
        b = []
        r_count = 0
        T = None
        w = 1
        m = 1
        for i, quad_idx in enumerate(self.Q):
            if self.Q_label[i]:
                T = lambda xy, m : m @ xy
                m = self.r[r_count]
                if type(scale) == np.ndarray:
                    m[:, 0] *= scale[0]
                    m[:, 1] *= scale[1]
                if type(saliency_map) == np.ndarray:
                    v = np.zeros((4, 2))
                    for j in range(4):
                        v[j] = self.origin_vertices[quad_idx[j]]
                    lb = v.min(axis=0).astype(np.int)
                    ub = v.max(axis=0).astype(np.int)
                    w = np.mean(saliency_map[lb[0]:ub[0],lb[1]:ub[1]])
                else:
                    w = w_f
                r_count += 1
            else:
                T = self.W
                m = 1
                w = 1
                
            for j in range(4):
                k = quad_idx[j]
                k_plus1 = quad_idx[(j+1) % 4]
                
                if self.idx_is_constraints[k] and self.idx_is_constraints[k_plus1]:
                    continue
                
                rhs = w * (T(self.origin_vertices[k_plus1], m) - T(self.origin_vertices[k], m))

                if self.idx_is_constraints[k]:
                    rhs += w * self.V[k]
                
                if self.idx_is_constraints[k_plus1]:
                    rhs += -w * self.V[k_plus1]
                
                b.append(rhs)
        for i in range(self.nq_row):
            if i == 0 or i == self.nq_row - 1:
                continue
            first = False
            for j in range(self.nq_col - 1):
                if j == 0 or j == self.nq_col - 2:
                    continue
                q = i * self.nq_col + j
                if (not first) and (not self.Q_label[q]):
                    first = True
                elif first and (not self.Q_label[q]):
                    b.append([0., 0.])
        for i in range(self.nq_col):
            if i == 0 or i == self.nq_col - 1:
                continue
            first = False
            for j in range(self.nq_row - 1):
                if j == 0 or j == self.nq_row - 2:
                    continue
                q = j * self.nq_col + i
                if (not first) and (not self.Q_label[q]):
                    first = True
                elif first and (not self.Q_label[q]):
                    b.append([0., 0.])
                
        self.b = np.array(b).astype(np.float32)







    def update_r(self):
        """
        update rigid transformation matrices
        self: mesh
        This is the original update_r function, no restrictions on the scaling/rotation
        """
        r = []
        is_feature = (self.Q_label != 0)
        labels = self.Q_label[is_feature]
        ori_vertices = self.origin_vertices[self.Q][is_feature]
        war_vertices = self.warped_vertices[self.Q][is_feature]
        lamb_sum = np.array([0.0] * (self.max_num))
        lamb_count = np.array([0] * (self.max_num))
        
        for warped_ver, origin_ver, label in zip(war_vertices, ori_vertices, labels):
            v = np.mean(origin_ver, axis=0)
            v_prime = np.mean(warped_ver, axis=0)
            
            u = (origin_ver - v).transpose()
            u_prime = (warped_ver - v_prime).transpose()
            
            U, S, Vh = np.linalg.svd(u_prime @ np.linalg.pinv(u))
            lamb_sum[label - 1] += np.min(S)
            lamb_count[label - 1] += 1
            r.append((Vh.T) @ (U.T))
        
        lamb_avg = lamb_sum / lamb_count
        for i, label in enumerate(labels):
            r[i] *= lamb_avg[label - 1]
        
        self.r = r

    def update_r2(self):
        """
        update rigid transformation matrices
        self: mesh
        This is the new update_r function, with restrictions on the scaling(scale is always 1)
        """
        r = []
        is_feature = (self.Q_label != 0)
        ori_vertices = self.origin_vertices[self.Q][is_feature]
        war_vertices = self.warped_vertices[self.Q][is_feature]
        v_prime = ori_vertices - np.mean(ori_vertices, axis = 1, keepdims=True)
        u_prime = war_vertices - np.mean(war_vertices, axis = 1, keepdims=True)
        h = np.transpose(v_prime, [0, 2, 1]) @ u_prime
        
        for i in h:
            U, S, V = np.linalg.svd(i)
            r.append(V @ U.T)
        self.r = r

    def quad_to_coor(self, reverse=False):
        """
        generate a coordinate mapping from the given mesh and vertex coordinates
        self: mesh
        V: vertex coordinates
        target_size: target size
        reverse: whether to reverse the coordinate mapping
        mapping: ndarray of shape (*target_size, 2), value (x, y) at location mapping(i, j) means
        target_image[i, j] = original_image[x, y]
        """
        if not reverse:
            mapping = np.ones((*self.target_size, 2)) * -1
        else:
            mapping = np.ones((*self.saliency_map.shape, 2)) * -1
        for quad in self.Q:
            if not reverse:
                src = np.array(self.origin_vertices[quad]).astype(np.float32)
                dst = np.array(self.V[quad]).astype(np.float32)
            else:
                dst = np.array(self.origin_vertices[quad]).astype(np.float32)
                src = np.array(self.V[quad]).astype(np.float32)
            new_src, new_dst = (src - src.min(axis=0)).astype(np.float32), (dst - dst.min(axis=0)).astype(np.float32)
            
            dst_min = dst.min(axis=0).astype(np.int32)
            dst_max = dst.max(axis=0).astype(np.int32)
            dsize = dst_max - dst_min + 1
            dsize = (dsize[0], dsize[1])
            mask = np.zeros(dsize, dtype=np.uint8)
            cv2.fillConvexPoly(mask, np.array([new_dst[:,::-1]]).astype(np.int32), True)
            coors = np.where(mask == True)
            coors = np.stack(coors, axis=0)
            coors_in_warped = coors + dst_min.reshape(2, 1)
            
            M = cv2.getPerspectiveTransform(new_src[:,::-1], new_dst[:,::-1], cv2.DECOMP_SVD)
            M_inv = np.linalg.inv(M)
            coors = np.stack([coors[1,:], coors[0,:], np.ones((coors.shape[1]))], axis=0)
            coors = M_inv @ coors
            coors /= coors[2, :].reshape(1, -1)
            coors = np.stack([coors[1,:], coors[0,:]], axis=0)
            coors += src.min(axis=0).reshape(2,1)
            #TODO interpolate for invalid points
            # w_x = coors_in_warped[0,:]
            # w_y = coors_in_warped[1,:]
            # if not reverse:
            #     valid = (w_x >= 0) * (w_x < self.target_size[0]) * (w_y >= 0) * (w_y < self.target_size[1])
            # else:
            #     valid = (w_x >= 0) * (w_x < self.height) * (w_y >= 0) * (w_y < self.width)
            # coors_in_warped = coors_in_warped[:, valid]
            # coors = coors[:,valid]


            if not reverse:
                coors_in_warped[0, :] = np.clip(coors_in_warped[0, :], 0, self.target_size[0] - 1)
                coors_in_warped[1, :] = np.clip(coors_in_warped[1, :], 0, self.target_size[1] - 1)
            else:
                coors_in_warped[0, :] = np.clip(coors_in_warped[0, :], 0, self.height - 1)
                coors_in_warped[1, :] = np.clip(coors_in_warped[1, :], 0, self.width - 1)
            mapping[(coors_in_warped[0,:], coors_in_warped[1,:])] = coors.T
        return mapping


    def plot_mesh(self):
        """
        plot the mesh
        self: mesh
        V: vertex coordinates
        """
        tmp = self.V.reshape(self.nq_row+1, (self.nq_col+1), 2)
        plt.figure(figsize=(6,6))
        plt.gca().set_aspect('equal', adjustable='box')
        
        for r in range(self.nq_row+1):
            plt.plot(tmp[r][:, 1], tmp[r][:, 0], c='gray')
        for c in range(self.nq_col+1):
            plt.plot(tmp[:, c][:, 1], tmp[:, c][:, 0], c='gray')

        plt.gca().invert_yaxis()
        plt.show()
    
    def solve_and_update(self):
        ret = self.warped_vertices.copy()
        x = lsqr(self.L, self.b[:, 0])[0]
        y = lsqr(self.L, self.b[:, 1])[0]
        
        for i, idx in enumerate(self.non_constraints_idx):
            ret[idx, :] = x[i], y[i]
        
        self.V = ret

    def generate_mapping(self, w_f, original_size, compressed_size, scale=None):
        self.init_r(np.sum(self.Q_label != 0))
        self.compute_L2(w_f, self.saliency_map)
        self.V = self.warped_vertices.copy()
        self.compute_b2(w_f, self.saliency_map, scale)
        self.solve_and_update()
        self.update_r2()
        s = np.array([compressed_size]) / np.array([original_size])
        self.V += (np.array([compressed_size]) - 1) / 2
        self.coor_mapping = self.quad_to_coor()
        self.reverse_mapping = self.quad_to_coor(reverse=True)
    
    def coor_warping(self, img):
        """
        warp an image according to the given coordinate mapping
        foveated compression
        img: input image
        coor_mapping: coordinate mapping
        target_size: target size
        """
        out_img = np.zeros((*self.target_size, 3), dtype=np.uint8)
        coordinates = np.round(self.coor_mapping).astype(int)
        
        #print("warp", np.sum(np.logical_not(mask)))
        coordinates[:,:, 0] = np.clip(coordinates[:,:, 0], 0, img.shape[0] - 1)
        coordinates[:,:, 1] = np.clip(coordinates[:,:, 1], 0, img.shape[1] - 1)
        mask = np.nonzero(np.all(coordinates != -1, axis=2))
        filtered_coor = coordinates[mask]
        out_img[mask] = img[(filtered_coor[:,0], filtered_coor[:,1])]
        return out_img

    def reverse_warping(self, warped_img):
        """
        reverse the warped image to recover the original image
        reverse foveated compression
        img: input image
        coor_mapping: coordinate mapping
        target_size: target size
        """
        out_img = np.zeros((*self.saliency_map.shape, 3), dtype=np.uint8)
        coordinates = np.round(self.reverse_mapping).astype(int)
        
        #print("unwarp", np.sum(np.logical_not(mask)))
        coordinates[:,:, 0] = np.clip(coordinates[:,:, 0], 0, self.target_size[0] - 1)
        coordinates[:,:, 1] = np.clip(coordinates[:,:, 1], 0, self.target_size[1] - 1)
        mask = np.nonzero(np.all(coordinates != -1, axis=2))
        filtered_coor = coordinates[mask]
        out_img[mask] = warped_img[(filtered_coor[:,0], filtered_coor[:,1])]
        return out_img
    

class Gaussian():
    def __init__(self, mask_size):
        self.mask_size = mask_size
        params = cv2.SimpleBlobDetector_Params()
        params.minThreshold = 1
        params.minDistBetweenBlobs = mask_size[0]//100
        self.detector = cv2.SimpleBlobDetector_create(params)
    
    def gaussian(self, x, amp, x0, y0, sx, sy, r):
        return amp * np.exp(-1 * (
            (x[:,0]-x0)**2 / (2 * sx ** 2)+ 
            (x[:,1]-y0)**2 / (2 * sy ** 2) -
            2 * r * (x[:,0]-x0) / sx * (x[:,1]-y0)/ sy
            ))

    def fit_func(self, x, *args):
        arr = np.zeros(x.shape[0])
        for i in range(len(args)//6):
            arr += self.gaussian(x, *args[i*6 : i*6 + 6])
        return arr

    def parameterize(self, original_mask, threshold):
        keypoints = self.detector.detect(255 - original_mask)
        p0 = [[original_mask[int(i.pt[1])][int(i.pt[0])], int(i.pt[1]), int(i.pt[0]), i.size/2, i.size/2, 0] for i in keypoints]
        bounds = [[(original_mask[int(i.pt[1])][int(i.pt[0])] - 20, original_mask[int(i.pt[1])][int(i.pt[0])] + 20), 
                (int(i.pt[1]) - 10, int(i.pt[1]) + 10), 
                (int(i.pt[0]) - 10, int(i.pt[0]) + 10), 
                (1, i.size), 
                (1, i.size),
                (-1, 1)] for i in keypoints]
        fit_mask = np.nonzero(original_mask >= threshold)
        fit_x = np.stack(fit_mask, axis=1)
        fit_y = original_mask[fit_mask].astype(np.float64)
        popt, pcov = curve_fit(self.fit_func, fit_x, fit_y, p0)
        self.popt = popt
        return popt
    
    def extract_centers(self):
        center_points = np.zeros((len(self.popt)//6, 2))
        for i in range(len(self.popt)//6):
            center_points[i, 0] = self.popt[i * 6 + 1]
            center_points[i, 1] = self.popt[i * 6 + 2]
        return center_points
    
    def build_map_from_params(self):
        fit = np.zeros(self.mask_size)
        fit_x = np.where(fit == 0)
        fit_x = np.stack(fit_x, axis=1)
        for i in range(len(self.popt)//6):
            fit += self.gaussian(fit_x, *self.popt[i*6:i*6+6]).reshape(self.mask_size)
        return fit
    
    def build_new_map_from_params(self):
        npopt = self.popt.copy()
        fit = np.zeros(self.mask_size)
        fit_x = np.where(fit == 0)
        fit_x = np.stack(fit_x, axis=1)
        for i in range(len(npopt)//6):
            npopt[i*6 + 3:i*6+5] *= 1.5
            fit += self.gaussian(fit_x, *npopt[i*6:i*6+6]).reshape(self.mask_size)
        return fit
    
    def from_parameters(self, popt):
        self.popt = popt

def rescale3(coor, height_multiplier, width_multiplier, img_size):
    coor = coor.copy()
    if coor.shape == (2,):
        coor[0] = coor[0] * height_multiplier
        coor[1] = coor[1] * width_multiplier
    else:
        coor[:, 0] = coor[:, 0] * height_multiplier
        coor[:, 1] = coor[:, 1] * width_multiplier
    return coor

def rescale(coor, height_multiplier, width_multiplier, img_size):
    coor = coor.copy()
    if coor.shape == (2,):
        coor[0] = (coor[0] - (img_size[0] - 1) / 2) * height_multiplier
        coor[1] = (coor[1] - (img_size[1] - 1) / 2) * width_multiplier
    else:
        coor[:, 0] = (coor[:, 0] - (img_size[0] - 1) / 2) * height_multiplier
        coor[:, 1] = (coor[:, 1] - (img_size[1] - 1) / 2) * width_multiplier
    return coor




def salient_scale(mask, shape, target_scale, margin=0.1):
    mask = np.where(mask != 0)
    mask = np.stack(mask, axis=1)
    lb = mask.min(axis = 0)
    ub = mask.max(axis = 0)
    r = ((ub - lb) / np.array(shape).reshape(1, 2))
    r = r + 2 * margin
    required_scale = target_scale / r
    result = np.ones(2)
    for i in range(2):
        if required_scale[0, i] < 1:
            # ln(1 + x) < x where x is the shrinked percentage 
            # or just x?
            #result[i] = 1 - np.log(2 - required_scale[0, i])
            result[i] = required_scale[0, i]
    return result