from torch.utils.data import Dataset
from torchvision.transforms import transforms
import pandas as pd
import torch
from PIL import Image
import numpy as np
from joblib import Parallel, delayed
import cv2


class HealthDataset(Dataset):
    def __init__(self, label_path, img_path, transform=None, target_transform=None, load_ram=True):
        self.df = pd.read_csv(label_path, header=0)
        self.df_contains_label = True if 'label' in self.df.columns else False
        if self.df_contains_label:
            self.labels = torch.FloatTensor([0 if label == "negative" else 1 for label in self.df["label"]]).squeeze()
        else:
            self.labels = self.df["image"].tolist()
        self.names = self.df["image"].tolist()
        self.transform = transform
        self.target_transform = target_transform
        self.image_path=img_path
        # load img to ram
        if load_ram:
            self.images = []
            #for name in self.names:
            #    image = Image.open(self.image_path + name)
            #    trans = np.stack((image, image, image), 2)
            #    self.images.append(Image.fromarray(trans.astype(np.uint8), mode="RGB"))
            self.images = Parallel(n_jobs=20)(delayed(self.preproc_image)(self.image_path + name) for name in self.names)
        self.load_ram = load_ram

    def preproc_image(self, image_path):
        image = Image.open(image_path)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        image = clahe.apply(np.array(image))
        trans = np.stack((image, image, image), 2)
        return Image.fromarray(trans.astype(np.uint8), mode="RGB")

    def load_image(self, idx: int) -> torch.Tensor:
        if self.load_ram:
            return self.images[idx].copy()
        else:
            return self.preproc_image(self.image_path + self.names[idx])

    def __len__(self):
        return self.labels.shape[0]

    def __getitem__(self, idx):
        image = self.load_image(idx)
        label = self.labels[idx]
        if self.transform:
            image = self.transform(image)
        if self.target_transform:
            label = self.target_transform(label)
        return image, label


if __name__ == "__main__":
    transform = transforms.Compose(
            [transforms.RandomEqualize(p=1.0),
             transforms.Resize((320, 320)),
             ]
        )
    dataset = HealthDataset(label_path="/hkfs/work/workspace/scratch/im9193-H5/data/valid.csv", img_path = "/hkfs/work/workspace/scratch/im9193-H5/data/imgs/",transform=transform, load_ram=False)

    data_dir = "/hkfs/work/workspace/scratch/im9193-H5/tmp/"
    for i in range(150):
        try:
            img, _ = dataset.__getitem__(i)
            print(img.size)
            PIL_image = Image.fromarray(np.array(img), mode="RGB")
            print(PIL_image.size)
            PIL_image = PIL_image.convert("L")
            PIL_image.save(data_dir + f"{i}.png")
        except:
            continue

