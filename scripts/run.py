import os
import click
import numpy as np
from pathlib import Path
from shutil import copyfile
from omegaconf import OmegaConf, DictConfig
from glob import glob
import hydra

backup_file_patterns = [
    './CMakeLists.txt',
    './*.cpp', './*.h', './*.cu',
    './src/*.cpp', './src/*.h', './src/*.cu',
    './src/*/*.cpp', './src/*/*.h', './src/*/*.cu',
    './src/*/*/*.cpp', './src/*/*/*.h', './src/*/*/*.cu',
]


def make_image_list(data_path, factor):
    image_list = []
    suffix = ['*.jpg', '*.png', '*.JPG', '*.jpeg']

    # build image directory path
    if 0.999 < factor < 1.001:
        image_dir_name = "images"
        if os.path.isdir(os.path.join(data_path, image_dir_name)) is False:
            image_dir_name = "images_1"
    else:
        f_int = int(np.round(factor))
        image_dir_name = 'images_{}'.format(f_int)
    image_dir_path = os.path.join(data_path, image_dir_name)

    # build image list
    registered_image_list = os.path.join(data_path, 'registered_image_list.npy')
    if os.path.exists(registered_image_list):
        print("load image list from {}".format(registered_image_list))
        registered_image_list = np.load(registered_image_list, allow_pickle=True).tolist()
        for i in registered_image_list:
            image_list.append(os.path.join(image_dir_path, i))
    else:
        for suf in suffix:
            image_list += list(Path(image_dir_path).rglob(suf))

    assert len(image_list) > 0, "No image found"
    image_list.sort()

    f = open(os.path.join(data_path, 'image_list.txt'), 'w')
    for image_path in image_list:
        f.write(str(image_path) + '\n')


@hydra.main(version_base=None, config_path='../confs', config_name='default')
def main(conf: DictConfig) -> None:
    if 'work_dir' in conf:
        base_dir = conf['work_dir']
    else:
        base_dir = os.getcwd()

    print('Working directory is {}'.format(base_dir))

    data_path = os.path.join(base_dir, 'data', conf['dataset_name'], conf['case_name'])
    base_exp_dir = os.path.join(base_dir, 'exp', conf['case_name'], conf['exp_name'])

    os.makedirs(base_exp_dir, exist_ok=True)

    # backup codes
    file_backup_dir = os.path.join(base_exp_dir, 'record/')
    os.makedirs(file_backup_dir, exist_ok=True)

    for file_pattern in backup_file_patterns:
        file_list = glob(os.path.join(base_dir, file_pattern))
        for file_name in file_list:
            new_file_name = file_name.replace(base_dir, file_backup_dir)
            os.makedirs(os.path.dirname(new_file_name), exist_ok=True)
            copyfile(file_name, new_file_name)

    make_image_list(data_path, conf['dataset']['factor'])

    conf = OmegaConf.to_container(conf, resolve=True)
    conf['dataset']['data_path'] = data_path
    conf['base_dir'] = base_dir
    conf['base_exp_dir'] = base_exp_dir

    OmegaConf.save(conf, os.path.join(file_backup_dir, 'runtime_config.yaml'))
    OmegaConf.save(conf, './runtime_config.yaml')

    for build_dir in ['build', 'cmake-build-release']:
        if os.path.exists('{}/{}/main'.format(base_dir, build_dir)):
            os.system('{}/{}/main'.format(base_dir, build_dir))
            return

    assert False, 'Can not find executable file'


if __name__ == '__main__':
    main()
