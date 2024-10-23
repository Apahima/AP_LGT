import os
import sys

from torch.utils.data import DataLoader



from src.datasets.dmr_dataset import DMRDataset,DMRDatasetAnnotated, DMRDatasetClassification, DMR_gray, DMRDatasetAnnotatedGray,DMRDatasetClassificationGray


from src.utils.attribute_hashmap import AttributeHashmap



from CUTS.src.data_utils.extend import ExtendedDataset
from CUTS.src.data_utils.split import split_dataset


def prepare_dataset(config: AttributeHashmap, mode: str = 'train',binary=False):
    # Read dataset.

    if config.dataset_name == 'DMR':
        dataset = DMRDataset(base_path=config.dataset_path)
    elif config.dataset_name == 'DMR Annotated':
        dataset = DMRDatasetAnnotated(base_path=config.dataset_path)
    elif config.dataset_name == 'DMR Annotated Gray':
        dataset = DMRDatasetAnnotatedGray(base_path=config.dataset_path)

    elif config.dataset_name == 'DMR Classification':
        dataset = DMRDatasetClassification(base_path=config.dataset_path)
    elif config.dataset_name == 'DMR Classification Gray':
        dataset = DMRDatasetClassificationGray(base_path=config.dataset_path)
    elif config.dataset_name == 'DMR_gray':
        dataset = DMR_gray(base_path=config.dataset_path)
    
    else:
        raise Exception(
            'Dataset not found. Check `dataset_name` in config yaml file.')

    num_image_channel = dataset.num_image_channel()
    '''
    Dataset Split.
    Something special here.
    Since the method is unsupervised/self-supervised, we believe it is justifiable to:
        (1) Split the dataset to a train set and a validation set when training the model.
        (2) Use the entire dataset as the test set for evaluating the segmentation performance.
    We believe this is reasonable because ground truth label is NOT used during the training stage.
    '''
    # Load into DataLoader
    if mode == 'train':
        ratios = [float(c) for c in config.train_val_ratio.split(':')]
        ratios = (1.0,0.0) if binary else tuple([c / sum(ratios) for c in ratios])
        train_set, val_set = split_dataset(dataset=dataset,
                                           splits=ratios,
                                           random_seed=config.random_seed,binary_classification=binary)

        min_batch_per_epoch = 5
        desired_len = max(len(train_set),
                          config.batch_size * min_batch_per_epoch)
        train_set = ExtendedDataset(dataset=train_set, desired_len=desired_len)

        train_set = DataLoader(dataset=train_set,
                               batch_size=config.batch_size,
                               shuffle=True,
                               num_workers=config.num_workers)
        val_set = DataLoader(dataset=val_set,
                             batch_size=config.batch_size,
                             shuffle=False,
                             num_workers=config.num_workers)
        return train_set, val_set, num_image_channel
    else:
        test_set = DataLoader(dataset=dataset,
                              batch_size=config.batch_size,
                              shuffle=False,
                              num_workers=config.num_workers)
        return test_set, num_image_channel


def prepare_dataset_supervised(config: AttributeHashmap):
    # Read dataset.
    if config.dataset_name == 'DMR':
        dataset = DMRDatasetAnnotated(base_path=config.dataset_path)
    #elif config.dataset_name == 'retina':
    #    dataset = Retina(base_path=config.dataset_path)
    #elif config.dataset_name == 'berkeley':
    #    dataset = BerkeleyNaturalImages(base_path=config.dataset_path)
    #elif config.dataset_name == 'brain_ventricles':
    #    dataset = BrainVentricles(base_path=config.dataset_path)
    #elif config.dataset_name == 'brain_tumor':
    #    dataset = BrainTumor(base_path=config.dataset_path)
    #else:
    #    raise Exception(
     #       'Dataset not found. Check `dataset_name` in config yaml file.')

    num_image_channel = dataset.num_image_channel()
    num_classes = dataset.num_classes()

    # Load into DataLoader
    ratios = [float(c) for c in config.train_val_test_ratio.split(':')]
    ratios = tuple([c / sum(ratios) for c in ratios])
    train_set, val_set, test_set = split_dataset(
        dataset=dataset, splits=ratios, random_seed=config.random_seed)

    min_batch_per_epoch = 5
    desired_len = max(len(train_set), config.batch_size * min_batch_per_epoch)
    train_set = ExtendedDataset(dataset=train_set, desired_len=desired_len)

    train_set = DataLoader(dataset=train_set,
                           batch_size=config.batch_size,
                           shuffle=True,
                           num_workers=config.num_workers)
    val_set = DataLoader(dataset=val_set,
                         batch_size=len(val_set),
                         shuffle=False,
                         num_workers=config.num_workers)
    test_set = DataLoader(dataset=test_set,
                          batch_size=len(test_set),
                          shuffle=False,
                          num_workers=config.num_workers)
    return train_set, val_set, test_set, num_image_channel, num_classes
