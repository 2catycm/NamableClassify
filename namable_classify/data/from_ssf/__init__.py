import lazy_loader


__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules={
        'cub2011',
        'dataset_factory',
        'loader',
        'nabirds',
        'stanford_dogs',
        'transforms_factory',
        'vtab',
    },
    submod_attrs={
        'cub2011': [
            'Cub2011',
        ],
        'dataset_factory': [
            'create_dataset',
            'has_inaturalist',
            'has_places365',
        ],
        'loader': [
            'MultiEpochsDataLoader',
            'PrefetchLoader',
            'create_loader',
            'expand_to_chs',
            'fast_collate',
        ],
        'nabirds': [
            'NABirds',
            'get_continuous_class_map',
            'load_class_names',
            'load_hierarchy',
        ],
        'stanford_dogs': [
            'dogs',
        ],
        'transforms_factory': [
            'create_transform',
            'transforms_direct_resize',
            'transforms_imagenet_eval',
            'transforms_imagenet_train',
            'transforms_simpleaug_train',
        ],
        'vtab': [
            'DATA2CLS',
            'VtabDataset',
            'VtabSplit',
        ],
    },
)

__all__ = ['Cub2011', 'DATA2CLS', 'MultiEpochsDataLoader', 'NABirds',
           'PrefetchLoader', 'VtabDataset', 'VtabSplit', 'create_dataset',
           'create_loader', 'create_transform', 'cub2011', 'dataset_factory',
           'dogs', 'expand_to_chs', 'fast_collate', 'get_continuous_class_map',
           'has_inaturalist', 'has_places365', 'load_class_names',
           'load_hierarchy', 'loader', 'nabirds', 'stanford_dogs',
           'transforms_direct_resize', 'transforms_factory',
           'transforms_imagenet_eval', 'transforms_imagenet_train',
           'transforms_simpleaug_train', 'vtab']
