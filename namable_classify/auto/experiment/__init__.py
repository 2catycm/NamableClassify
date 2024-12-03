import lazy_loader


__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules={
        'infra',
        'mutiple',
        'single',
    },
    submod_attrs={
        'infra': [
            'PostgresDatabaseConfig',
            'auto_exp_runs_path',
            'checkpoint_path',
            'database_config_path',
            'fixed_meta_parameters',
            'run_with_config',
            'sqlite_url',
            'study_path',
        ],
        'mutiple': [
            'backbone_name2pe',
            'database_name',
            'delta_to_try',
            'fixed_meta_parameters',
            'host',
            'objective',
            'password',
            'peft_to_try',
            'port',
            'postgres_url',
            'study',
            'study_results',
            'username',
            'yuequ_to_try',
        ],
        'single': [
            'backbone_name2pe',
            'delta_to_try',
            'objective',
            'peft_to_try',
            'study',
            'study_results',
            'yuequ_to_try',
        ],
    },
)

__all__ = ['PostgresDatabaseConfig', 'auto_exp_runs_path', 'backbone_name2pe',
           'checkpoint_path', 'database_config_path', 'database_name',
           'delta_to_try', 'fixed_meta_parameters', 'host', 'infra', 'mutiple',
           'objective', 'password', 'peft_to_try', 'port', 'postgres_url',
           'run_with_config', 'single', 'sqlite_url', 'study', 'study_path',
           'study_results', 'username', 'yuequ_to_try']
