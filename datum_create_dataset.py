#!/usr/bin/env python3

### Required:
# Datumaro
# unzip

import os
import os.path as osp
import random
import subprocess
import argparse
import logging as log
from multiprocessing import Pool, Manager
import configparser
from benedict import benedict
import shutil
from collections import OrderedDict

import pandas as pd

import cv2

import datumaro as dm
import datumaro.components.operations as dmop
from datumaro.plugins.transforms import Rename
from datumaro.components.operations import IntersectMerge

log.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=log.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

DATUM = 'datum'
PREFIX_VID = 'vid_'
PREFIX_CVAT = 'cvat_'
XML_ANNOTATIONS = 'annotations.xml'
XML_DEFAULT = 'default.xml'
SEQINFO = 'seqinfo.ini'

EMPTY_PROJ_PATH = 'empty_proj' # Path to empty proj with only correct labels

DUP_LABELS_MAPPING = {
        'White Fish': 'Whitefish',
        'Bull Trout': 'Bull',
        'Lan prey': 'Lamprey',
        'Lampray': 'Lamprey'
        }

KEY_ANNO = 'annotations'
KEY_LABELS = 'labels'
KEY_DISTRIB = 'distribution'

MERGE_SEQ_STATS = 'merge_seq_stats.json'
MERGE_SPECIES_COUNTER = 'merge_species_counter.json'

SEQ_STATS = 'seq_stats.json'
SPECIES_COUNTER = 'species_counter.json'

VALID_SPLIT_RATIO = 0.15
TEST_SPLIT_RATIO = 0.15
RANDOM_SEED = 198

class VidDataset:
    # Datumaro datasets
    vid_dataset = None
    cvat_dataset = None
    dataset = None

    # seqinfo.ini
    imDir = 'img1'
    frameRate = -1
    seqLength = -1
    imWidth = -1
    imHeight = -1
    imExt = '.jpg'

    def __init__(self, name: str, vid_path: str, args):
        self.proj_path = args.proj_path
        self.anno_path = args.anno_path
        #self.transform_path = args.transform_path
        self.ini_path = f'{remove_path_end(self.proj_path)}_inis'

        self.extract_frames(name, vid_path)

    def extract_frames(self, name: str, vid_path: str, overwrite=False):
        # Get data for the seqinfo.ini
        video = cv2.VideoCapture(vid_path)
        self.frameRate = video.get(cv2.CAP_PROP_FPS)
        self.imWidth = video.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.imHeight = video.get(cv2.CAP_PROP_FRAME_HEIGHT)

        # Extract frames to the project folder
        dest_path = osp.abspath(osp.join(self.anno_path, PREFIX_VID + name))

        if not overwrite and osp.exists(dest_path):
            log.info(f"Exists. Skip extracting {dest_path}")
            self._import_image_dir(dest_path)
            return

        log.info(f"Extracting frames {vid_path}")

        vid_data = dm.Dataset.import_from(
            vid_path,
            "video_frames",
            name_pattern='frame_%06d',
        )

        vid_data.export(format="image_dir", save_dir=dest_path, image_ext=self.imExt)

        self._import_image_dir(dest_path)

    def _import_image_dir(self, dest_path: str):
        _, _, files = next(os.walk(dest_path))
        self.seqLength = len(files)

        self.vid_dataset = dm.Dataset.import_from(
                dest_path,
                "image_dir"
                )

    def import_zipped_anno(self, name: str, anno_zip_path: str, overwrite=False):
        dest_path = osp.abspath(osp.join(self.anno_path, PREFIX_CVAT + name))
        if not overwrite and osp.exists(dest_path):
            log.info(f"Exists. Skipping unzip {dest_path}")
            self.cvat_dataset = dm.Dataset.import_from(dest_path, "cvat")
            return

        log.info("Unzipping and importing CVAT...")
        subprocess.run(['unzip', '-o', '-d', dest_path, anno_zip_path])

        # Rename to the default, so the annotations can be matched with the video frames
        os.rename(osp.join(dest_path, XML_ANNOTATIONS), osp.join(dest_path, XML_DEFAULT))
        self.cvat_dataset = dm.Dataset.import_from(dest_path, "cvat")

    def _transform(self, name: str, src_path: str, overwrite=False):
        dest_path = osp.join(self.transform_path, name.lower()) # Must be lowercase due to datumaro restrictions
        if not overwrite and osp.exists(dest_path):
            log.info(f"Exists. Skipping transform {dest_path}")
            return

        log.info(f"Renaming video frames to {dest_path}")
        subprocess.run([DATUM, 'transform', '-t', 'rename', '-o', dest_path,
            f"{src_path}:datumaro", '--', '-e', f"|^frame_|{name}_|"])

    def export_datum(self, name: str, overwrite=False):
        dest_path = osp.abspath(osp.join(self.proj_path, name.lower())) # Must be lowercase due to datumaro restrictions
        #self.dataset = dm.Dataset.from_extractors(self.vid_dataset, self.cvat_dataset)
        self.dataset = IntersectMerge()([self.vid_dataset, self.cvat_dataset])
        if not overwrite and osp.exists(dest_path):
            log.info(f"Exists. Skipping datum export {dest_path}")
            #self._transform(name, dest_path)
            return

        log.info(f"Exporting as datumaro to {dest_path}")
        self.dataset.export(dest_path, 'datumaro')

        #self._transform(name, dest_path)

    def gen_seqinfo(self, name: str, overwrite=False):
        # Generate seqinfo.ini file
        seq_path = osp.abspath(osp.join(self.ini_path, name.lower(), SEQINFO))
        if not overwrite and osp.exists(seq_path):
            log.info(f"Exists. Skip generating {seq_path}")
            return

        log.info(f'Generating seqinfo.ini file to {seq_path}')

        d = benedict()
        d['Sequence'] = {}
        seq = d['Sequence']

        seq['name'] = name
        seq['imDir'] = self.imDir
        seq['frameRate'] = int(self.frameRate)
        seq['seqLength'] = int(self.seqLength)
        seq['imWidth'] = int(self.imWidth)
        seq['imHeight'] = int(self.imHeight)
        seq['imExt'] = self.imExt

        d.to_ini(filepath=seq_path)

def filename_to_name(filename):
    return filename.replace(' ', '_')

def remove_path_end(path: str):
    return path[:-1] if path.endswith('/') else path

def export_vid(row_tuple):
    row = row_tuple[1]
    name = filename_to_name(row.filename)
    vid_data = VidDataset(name, row.vid_path, args)
    vid_data.import_zipped_anno(name, row.anno_path)
    vid_data.export_datum(name)
    vid_data.gen_seqinfo(name)
    #vid_data.export_mot(name)

#class SeqDistrib:
#    name = ""
#    stats = {}
#
#    def __init__(self, name, stats):
#        self.name = name
#        self.stats = stats

class MergeExport:
    dataset_merged = None
    dataset_empty = None
    rand = random.Random(RANDOM_SEED)

    seq_stats = {}
    species_counter = {}
    merge_seq_stats = {}
    merge_species_counter = {}

    def __init__(self, name_df: pd.DataFrame, src_path: str, export_path: str, jobs: int):
        self.df = name_df
        self.src_path = osp.abspath(src_path)
        self.ini_path = osp.abspath(f'{remove_path_end(src_path)}_inis')
        self.merge_path = osp.abspath(f'{remove_path_end(src_path)}_merged')
        self.preprocess_path = osp.abspath(f'{self.merge_path}_preprocess')

        self.vid_path = osp.abspath(f'{self.merge_path}_vids')
        self.export_path = osp.abspath(export_path)
        self.jobs = jobs
        self.dataset_empty = osp.abspath(EMPTY_PROJ_PATH)

    @staticmethod
    def _merge_vid_job(row_tuple):
        _, row, src_path, dest_folder, dataset_empty_path, overwrite = row_tuple

        name = filename_to_name(row.filename).lower()
        dest_path = osp.join(dest_folder, name.lower())

        if not overwrite and osp.exists(dest_path):
            log.info(f"Exists. Skipping merge {dest_path}")
            return

        seq_path = osp.join(src_path, name)
        data = dm.Dataset.import_from(seq_path, "datumaro")
        dataset_empty = dm.Dataset.import_from(dataset_empty_path, "datumaro")
        dataset_merged = IntersectMerge()([data, dataset_empty])

        # Fix duplicate labels
        dataset_merged.transform('remap_labels', mapping=DUP_LABELS_MAPPING)

        dataset_merged.export(format='datumaro', save_dir=dest_path)

    def merge_dataset(self, overwrite=False):
        """
        Merge the separated video datasets into one to deal with inconsistent labels
        """
        log.info('Merging transformed dataset...')

        jobs_pool = Pool(self.jobs)
        manager = Manager()
        seq_stats = manager.dict()
        species_counter = manager.dict()
        count_lock = manager.Lock()

        row_merged_tuples = [tup + (self.src_path, self.merge_path, self.dataset_empty, overwrite) for tup in self.df.iterrows()]
        jobs_pool.map(self._merge_vid_job, row_merged_tuples)

        jobs_pool.close()
        jobs_pool.join()

    @staticmethod
    def _preprocess_job(row_tuple):
        _, row, src_path, dest_folder, overwrite = row_tuple

        name = filename_to_name(row.filename).lower()
        dest_path = osp.join(dest_folder, name.lower())
        if not overwrite and osp.exists(dest_path):
            log.info(f"Exists. Skip preprocessing {dest_path}")
            return

        log.info(f'Preprocessing {dest_path}')
        seq_path = osp.join(src_path, name)
        data = dm.Dataset.import_from(seq_path, "datumaro")
        dataset_filtered_wide = dm.Dataset.filter(data, '/item[annotation/w > annotation/h] | /item[not(annotation)]')

        dataset_filtered_wide.export(format='datumaro', save_dir=dest_path)

    def preprocess(self, overwrite=False):
        """
        Preprocess dataset (Removing tiny/incorrect boxes, etc.)
        """
        log.info('Preprocessing dataset...')
        jobs_pool = Pool(self.jobs)

        row_merged_tuples = [tup + (self.merge_path, self.preprocess_path, \
                overwrite) for tup in self.df.iterrows()]
        jobs_pool.map(self._preprocess_job, row_merged_tuples)

        jobs_pool.close()
        jobs_pool.join()

    @staticmethod
    def _get_stats_job(row_tuple):
        _, row, src_path, seq_stats, species_counter, count_lock = row_tuple

        name = filename_to_name(row.filename).lower()
        seq_path = osp.join(src_path, name)
        log.info(f"Get stats from {seq_path}")
        data = dm.Dataset.import_from(seq_path, "datumaro")

        stats = dmop.compute_ann_statistics(data)
        cat_distribs = stats[KEY_ANNO][KEY_LABELS][KEY_DISTRIB]
        
        seq_ds = (name, cat_distribs)
        for categ, count in cat_distribs.items():
            if categ not in species_counter.keys():
                species_counter[categ] = 0
            if categ not in seq_stats.keys():
                seq_stats[categ] = []
            if count[0] == 0:
                continue

            count_lock.acquire()
            temp_stats = seq_stats[categ]
            temp_stats.append(seq_ds)
            seq_stats[categ] = temp_stats
            species_counter[categ] += count[0]
            count_lock.release()

    def _get_seq_set(self, max_counts, counts):
        out_seqs = []

        # Fill capacity with each sequence until each category is full
        for categ, seqs in self.seq_stats.items():
            if not categ in counts:
                counts[categ] = 0
            for i in range(len(seqs)):
                if counts[categ] >= max_counts[categ]:
                    break
                seq = seqs.pop()
                if seq[0] in out_seqs:
                    continue
                counts = self._count_categs(seq, counts)
                out_seqs.append(seq[0])

        # Remove sequences taken out
        for categ in self.seq_stats.keys():
            self.seq_stats[categ] = [seq for seq in self.seq_stats[categ] if seq[0] not in out_seqs]

        return (out_seqs, counts)

    def _count_categs(self, seq, counts):
        for in_categ, count in seq[1].items():
            if count[0] <= 0:
                continue
            if not in_categ in counts:
                counts[in_categ] = 0
            counts[in_categ] += count[0]
        return counts

    @staticmethod
    def _to_json(_d, target_path):
        d = benedict(_d)
        d.to_json(filepath=target_path)


    def stratified_split(self, src_path, skip_preprocess=False, overwrite=False):
        """
        Split the dataset into train, valid, and test sets using random stratified splitting
        """
        self.split_path = osp.abspath(f'{src_path}_train_split')
        if not overwrite and osp.exists(self.split_path):
            log.info(f"Exists. Skipping stratified split {self.split_path}")
            return
        log.info('Getting stats...')
        jobs_pool = Pool(self.jobs)
        manager = Manager()
        seq_stats = manager.dict()
        species_counter = manager.dict()
        count_lock = manager.Lock()

        row_merged_tuples = [tup + (src_path, \
                seq_stats, species_counter, count_lock) for tup in self.df.iterrows()]
        jobs_pool.map(self._get_stats_job, row_merged_tuples)

        jobs_pool.close()
        jobs_pool.join()

        self.seq_stats = OrderedDict(sorted(seq_stats.items()))
        self.species_counter.update(species_counter)
        log.info('Performing stratified split...')

        # Save dicts
        #self._to_json(self.seq_stats, osp.join(self.preprocess_path, SEQ_STATS))
        #self._to_json(self.species_counter, osp.join(self.preprocess_path, SPECIES_COUNTER))
        #if skip_preprocess:
        #    if not self.merge_seq_stats:
        #        self.merge_seq_stats = OrderedDict(sorted(benedict.from_json(osp.join(self.merge_path, MERGE_SEQ_STATS)).items()))
        #        self.merge_species_counter = dict(benedict.from_json(osp.join(self.merge_path, MERGE_SPECIES_COUNTER)))
        #    self.species_counter = self.merge_species_counter
        #    self.seq_stats = self.merge_seq_stats
        #else:
        #    if not self.seq_stats:
        #        self.seq_stats = sorted(OrderedDict(benedict.from_json(osp.join(self.preprocess_path, SEQ_STATS))))
        #        self.species_counter = dict(benedict.from_json(osp.join(self.preprocess_path, SPECIES_COUNTER)))

        train_path = osp.join(self.split_path, 'train')
        valid_path = osp.join(self.split_path, 'valid')
        test_path = osp.join(self.split_path, 'test')

        # Find distrib of categories
        sum_counts = sum(self.species_counter.values())
        valid_max_counts = {}
        test_max_counts = {}
        for categ, count in self.species_counter.items():
            # Get specific max counts for each set
            valid_max_counts[categ] = int(count * VALID_SPLIT_RATIO)
            test_max_counts[categ] = int(count * TEST_SPLIT_RATIO)
        

        # Shuffle seq category stats dict
        for categ in self.seq_stats.keys():
            # Sort first to elicit reproducibility
            self.seq_stats[categ].sort(key=lambda x: x[0])
            self.rand.shuffle(self.seq_stats[categ])

        # Every set should have at least one seq of every category
        def add_one_categ():
            dataset_seqs = []
            counts = {}
            for seqs in self.seq_stats.values():
                for i in range(len(seqs)):
                    try:
                        seq = seqs.pop()
                    except:
                        continue
                    if seq[0] not in dataset_seqs:
                        dataset_seqs.append(seq[0])
                        counts = self._count_categs(seq, counts)
                        break

            # Remove
            for categ in self.seq_stats.keys():
                self.seq_stats[categ] = [seq for seq in self.seq_stats[categ] if seq[0] not in dataset_seqs]
            return dataset_seqs, counts

        # Add one each to account for very small datasets
        test_seqs, test_counts = add_one_categ()
        valid_seqs, valid_counts = add_one_categ()
        train_seqs, train_counts = add_one_categ()

        # Accumulate sequences until max capacity
        test_chosen_seqs, test_counts = self._get_seq_set(test_max_counts, test_counts)
        test_seqs += test_chosen_seqs

        valid_chosen_seqs, valid_counts = self._get_seq_set(valid_max_counts, valid_counts)
        valid_seqs += valid_chosen_seqs


        # Export the rest as train set
        for categ, seqs in self.seq_stats.items():
            for seq in seqs:
                if seq[0] not in train_seqs:
                    self._count_categs(seq, train_counts)
                    train_seqs.append(seq[0])  

        log.info('Test')
        log.info(len(test_seqs))
        log.info(test_counts)
        log.info(f"Max: {test_max_counts}")
        log.info('Valid')
        log.info(len(valid_seqs))
        log.info(valid_counts)
        log.info(f"Max: {valid_max_counts}")
        log.info('Train')
        log.info(len(train_seqs))
        log.info(train_counts)
        #log.info(f"Max: {train_max_counts}")

        def copy_seq(seqs, set_path):
            # Copy seqs to respective folders
            for name in seqs:
                shutil.copytree(osp.join(src_path, name), osp.join(set_path, name))

        copy_seq(valid_seqs, valid_path)
        copy_seq(test_seqs, test_path)
        copy_seq(train_seqs, train_path)

        self._to_json(self.species_counter, osp.join(self.split_path, 'distribution.json'))
        self._to_json(test_counts, osp.join(self.split_path, 'test_distribution.json'))
        self._to_json(valid_counts, osp.join(self.split_path, 'valid_distribution.json'))
        self._to_json(train_counts, osp.join(self.split_path, 'train_distribution.json'))

    @staticmethod
    def _split_vid_job(row_tuple):
        # Requires copying the merged dataset `jobs` number of times
        # TODO: If necessary to lower memory costs, do half of the jobs sequentially
        _, row, merged_path, dest_folder = row_tuple
        name = filename_to_name(row.filename)
        dest_path = osp.join(dest_folder, name.lower())

        if osp.exists(dest_path):
            log.info(f"Exists. Skipping split to {name}")
            return

        merged_copy = dm.Dataset.import_from(merged_path)
        merged_copy.select(lambda item: item.id.startswith(name))

        # Convert back to normal image frame filenames
        merged_copy.transform('rename', regex=f'|^{name}_||')
        merged_copy.export(save_dir=dest_path, format='datumaro')

    def split_merged_dataset(self, overwrite=False):
        """
        Split the merged dataset into individual video frame datasets
        """
        merged_path = osp.abspath(self.merge_path)
        dest_folder = osp.abspath(self.vid_path)

        log.info('Splitting merged dataset into individual video frame datasets...')

        jobs_pool = Pool(self.jobs)

        # Read-only
        row_merged_tuples = [tup + (merged_path, dest_folder) for tup in self.df.iterrows()]
        jobs_pool.map(self._split_vid_job, row_merged_tuples)

        jobs_pool.close()
        jobs_pool.join()

    @staticmethod
    def _export_job(row_src_dest_tuple):
        src_path, dest_path, ini_path, exp_format, overwrite, save_images = row_src_dest_tuple
        name = osp.basename(src_path)
        if not overwrite and osp.exists(dest_path):
            log.info(f"Exists. Skipping export to {dest_path}")
            return

        log.info(f"Exporting as {exp_format} to {dest_path}")
        dataset = dm.Dataset.import_from(src_path, format='datumaro')
        try:
            dataset.export(dest_path, exp_format, save_images=save_images)
        except Exception as e:
            log.info(f"Export failed for {dest_path}")

        if exp_format == 'mot_seq_gt':
            shutil.copyfile(osp.join(ini_path, name, SEQINFO), osp.join(dest_path, SEQINFO))

    def export(self, suffix, exp_format, overwrite=False, save_images=True):
        export_path = f"{self.export_path}_{suffix}"

        if exp_format == 'mot_seq_gt':
            export_path = osp.join(export_path, 'images')

        set_paths = ['train', 'valid',  'test']
        # Create a tuple of export path and src path with correct set
        seq_paths = [(osp.join(self.split_path, set_path, i), osp.join(export_path, set_path, i))
                for set_path in set_paths for i in os.listdir(osp.join(self.split_path, set_path))]

        export_pool = Pool(self.jobs)
        row_src_dest_tuples = [seq_path + (self.ini_path, exp_format, overwrite, save_images) for seq_path in seq_paths]
        export_pool.map(self._export_job, row_src_dest_tuples)
        export_pool.close()
        export_pool.join()


def main(args):
    df = pd.read_csv(args.csv_vids)
    os.makedirs(args.anno_path, exist_ok=True)
    os.makedirs(args.proj_path, exist_ok=True)
    #os.makedirs(args.transform_path, exist_ok=True)

    jobs_pool = Pool(int(args.jobs))
    row_tuples = df.iterrows()

    jobs_pool.map(export_vid, row_tuples)

    jobs_pool.close()
    jobs_pool.join()

    # merge_exp = MergeExport(df, args.proj_path, args.export_path, int(args.jobs))

    # Merge and split inconsistent annotations and labels
    # merge_exp.merge_dataset()
    # if not args.skip_preprocess:
    #     processed_path = merge_exp.preprocess_path
    #     merge_exp.preprocess()
    # else:
    #     processed_path = merge_exp.merge_path
    # merge_exp.stratified_split(processed_path, args.skip_preprocess)
    #merge_exp.split_merged_dataset()
    #merge_dataset(df.iterrows(), merged_path, args.transform_path)
    #split_merged_dataset(df.iterrows(), merged_path, int(args.jobs))

    # if (not args.export_off):
    #     # Export to final dataset
    #     merge_exp.export(args.format, args.format, args.exp_overwrite, not args.no_save_images)

if __name__ == '__main__':
    configparser.ConfigParser.optionxform = str

    parser = argparse.ArgumentParser(description='Combine videos and annotations and exports them into a Datumaro project.')

    parser.add_argument('csv_vids', help='CSV file of video and annotation .zip filepaths. Must have the columns `filename`, `vid_path`, and `anno_path`. `filename` must be a unique index.')
    parser.add_argument('--anno-path', default='annos', help='Annotations destination folder. Default: annos')
    parser.add_argument('--proj-path', default='datum_proj', help='Datumaro project destination folder. Default: datum_proj')
    #parser.add_argument('--transform-path', default='datum_proj_transform', help='Datumaro project transform destination folder. Default: datum_proj_transform')
    parser.add_argument('--export-off', action='store_true', help='Turn off exporting')
    parser.add_argument('--export-path', default='export', help='Export path. Will create an export of the supplied format eg. `export_yolo` if `-f yolo`. Default: export')
    parser.add_argument('--exp-overwrite', action='store_true', help='Overwrite export.')
    parser.add_argument('--no-save-images', action='store_true', help='Toggle on to not save images on export.')
    parser.add_argument('-s', '--skip-preprocess', action='store_true', help='Skip preprocessing.')
    parser.add_argument('-f', '--format', default='yolo', help='Export format. Check `datum export -h` for supported types. Default: yolo')
    parser.add_argument('-j', '--jobs', default='4', help='Number of jobs to run. Default: 4')
    parser.set_defaults(func=main)

    args = parser.parse_args()
    args.func(args)

# For each video
# Create a datumaro project
# Extract frames into a folder
# Add the folder as the `image_dir` format
# Unzip corresponding annotation file into a folder
# Add the folder as the `cvat` format
# Rename `annotations.xml` to `default.xml`
# Merge the two folders (Saving the images)
# Delete the frames and cvat folders
# Export as `mot_seq_gt`
# Generate a seqinfo.ini file