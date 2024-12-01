from enum import Enum
import os
import numpy as np
from torchvision.datasets.folder import ImageFolder, default_loader

DATA2CLS = {
    'caltech101': 102,
    'cifar(num_classes=100)': 100,
    'dtd': 47,
    'oxford_flowers102': 102,
    'oxford_iiit_pet': 37,
    'patch_camelyon': 2,
    'sun397': 397,
    'svhn': 10,
    'resisc45': 45,
    'eurosat': 10,
    'dmlab': 6,
    'kitti(task="closest_vehicle_distance")': 4,
    'smallnorb(predicted_attribute="label_azimuth")': 18,
    'smallnorb(predicted_attribute="label_elevation")': 9,
    'dsprites(predicted_attribute="label_x_position",num_classes=16)': 16,
    'dsprites(predicted_attribute="label_orientation",num_classes=16)': 16,
    'clevr(task="closest_object_distance")': 6,
    'clevr(task="count_all")': 8,
    'diabetic_retinopathy(config="btgraham-300")': 5
}

class VtabSplit(Enum):
    TRAIN = "train800.txt"
    VAL = "val200.txt"
    TEST = "test.txt"
    TRAIN_AND_VAL = "train800val200.txt"
    
class VtabDataset(ImageFolder):
    def __init__(self, vtab_dir,
                 subset_name = "cifar",
                 root = None, # override auto computed root
                #  train=True, 
                split:VtabSplit = VtabSplit.TRAIN, #
                 transform=None, target_transform=None, 
                 mode=None,is_individual_prompt=False,**kwargs):
        root = root or os.path.join(vtab_dir, subset_name)
        super().__init__(root=root, transform=transform, target_transform=target_transform, 
                         loader=default_loader, is_valid_file=None, allow_empty=False)
        # self.dataset_root = self.root
        # self.loader = default_loader
        # self.target_transform = None
        # self.transform = transform

        # train_list_path = os.path.join(self.dataset_root, 'train800val200.txt')
        # test_list_path = os.path.join(self.dataset_root, 'test.txt')

        
        # train_list_path = os.path.join(self.dataset_root, 'train800.txt')
        # test_list_path = os.path.join(self.dataset_root, 'val200.txt')
        
        list_path = os.path.join(self.root, split.value)

        self.samples = []
        self.labels = []
        
        with open(list_path, 'r') as f:
            for line in f:
                img_name = line.split(' ')[0]
                label = int(line.split(' ')[1])
                self.labels.append(label)
                self.samples.append((os.path.join(self.root, img_name), label))
        # classes (list): List of the class names sorted alphabetically.
        # class_to_idx (dict): Dict with items (class_name, class_index).
        # imgs (list): List of (image path, class_index) tuples
        self.classes = sorted(set(self.labels))
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}
        self.imgs = self.samples
    
    # def make_subset(self, subset_idx:np.ndarray):
    #     self.
