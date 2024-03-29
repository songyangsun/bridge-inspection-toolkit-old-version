import torch
from torch.utils.data import Dataset
import pandas as pd
import json
import os
from PIL import Image
from torchvision import transforms
from os.path import dirname
from bikit.utils import pil_loader
from pathlib import Path
from tqdm import tqdm

class CodebrimDataset(Dataset):
    """PyTorch Dataset for CODEBRIM Balanced. Multiclass-multilabel dataset with 6 classes.
    Dataset for Version 'CODEBRIM_classification_balanced_dataset.zip' from
    https://zenodo.org/record/2620293#.YILofIMzYUE."""
    bikit_path = Path(dirname(dirname(__file__)))

    with open(Path(os.path.join(bikit_path, "data/datasets.json"))) as f:
        DATASETS = json.load(f)

    def __init__(self, name="codebrim-classif-balanced", split=None, cache_dir=None, transform=None,
                 load_all_in_mem=False, devel_mode=False):
        """

        :param name: Dataset name.
        :param split: Use 'train', 'valid' or 'test.
        :param transform: Torch transformation for image data (this depends on your CNN).
        :param cache_dir: Path to cache_dir.
        :param load_all_in_mem: Whether or not to load all image data into memory (this depends on the dataset size and
            your memory). Loading all in memory can speed up your training.
        :param devel_mode:
        """

        assert name in list(self.DATASETS.keys()), f"This name does not exists. Use something from {list(DATASETS.keys())}."
        bikit_path = Path(dirname(dirname(__file__)))
        self.csv_filename = Path(os.path.join(bikit_path, "data", name) + ".csv")

        # Misc
        self.split = split
        if cache_dir:
            self.cache_full_dir = Path(os.path.join(cache_dir, name))
        else:
            self.cache_full_dir = Path(os.path.join(os.path.expanduser("~"), ".bikit", name))

        self.devel_mode = devel_mode
        self.class_names = ["Background", "Crack", "Spallation", "Efflorescence", "ExposedBars", "CorrosionStain"]
        self.num_classes = 6
        self.load_all_in_mem = load_all_in_mem

        # Data prep
        self.transform = transform
        self.df = pd.read_csv(self.csv_filename)
        if split:
            self.df = self.df[self.df["split_type"] == split]
        if devel_mode:
            self.df = self.df[:100]
        self.n_samples = self.df.shape[0]

        if load_all_in_mem:
            self.img_dict = {}
            for index, row in tqdm(self.df.iterrows(), total=self.df.shape[0], desc="Load images in memory"):
                img_filename = Path(os.path.join(self.cache_full_dir, row['img_path']))
                img_name = row['img_name']
                img = pil_loader(img_filename)
                self.img_dict[img_name] = img

    def __getitem__(self, index):
        """Returns image as torch.Tensor and label as torch.Tensor with dimension (bs, num_classes)
        where 1 indicates that the label is present."""
        data = self.df.iloc[index]

        # Get image
        if self.load_all_in_mem:
            img = self.img_dict[data['img_name']]
        else:
            img_filename = Path(os.path.join(self.cache_full_dir, data['img_path']))
            img = pil_loader(img_filename)
        if self.transform:
            img = self.transform(img)
        else:
            img = transforms.ToTensor()(img)

        # Get label with shape (6,)
        label = torch.FloatTensor(data[self.class_names].to_numpy().astype("float32"))
        return img, label

    def __len__(self):
        return self.n_samples

if __name__ == "__main__":
    print(__file__)
    train_dataset = CodebrimDataset(split="")
    train_dataset = CodebrimDataset(split="", load_all_in_mem=True)
    img, targets = train_dataset[0]
    print(img.shape, targets.shape)
    print(len(train_dataset))
    assert list(targets.shape) == [6]
    print("===Done===")