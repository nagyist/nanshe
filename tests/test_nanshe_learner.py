__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Aug 08, 2014 08:08:39 EDT$"


import json
import operator
import os
import shutil
import tempfile

import h5py
import numpy

import nanshe.expanded_numpy
import nanshe.HDF5_recorder

import synthetic_data

import nanshe.nanshe_learner


class TestNansheLearner(object):
    def setup(self):
        self.config_a_block = {
            "debug" : True,
            "generate_neurons" : {
                "postprocess_data" : {
                    "wavelet_denoising" : {
                        "remove_low_intensity_local_maxima" : {
                            "percentage_pixels_below_max" : 0
                        },
                        "wavelet_transform.wavelet_transform" : {
                            "scale" : 4
                        },
                        "accepted_region_shape_constraints" : {
                            "major_axis_length" : {
                                "max" : 25.0,
                                "min" : 0.0
                            }
                        },
                        "accepted_neuron_shape_constraints" : {
                            "eccentricity" : {
                                "max" : 0.9,
                                "min" : 0.0
                            },
                            "area" : {
                                "max" : 600,
                                "min" : 30
                            }
                        },
                        "denoising.estimate_noise" : {
                            "significance_threshhold" : 3.0
                        },
                        "denoising.significant_mask" : {
                            "noise_threshhold" : 3.0
                        },
                        "remove_too_close_local_maxima" : {
                            "min_local_max_distance" : 100.0
                        },
                        "use_watershed" : True
                    },
                    "merge_neuron_sets" : {
                        "alignment_min_threshold" : 0.6,
                        "fuse_neurons" : {
                            "fraction_mean_neuron_max_threshold" : 0.01
                        },
                        "overlap_min_threshold" : 0.6
                    }
                },
                "run_stage" : "all",
                "preprocess_data" : {
                    "normalize_data" : {
                        "simple_image_processing.renormalized_images" : {
                            "ord" : 2
                        }
                    },
                    "extract_f0" : {
                        "spatial_smoothing_gaussian_filter_stdev" : 5.0,
                        "which_quantile" : 0.5,
                        "temporal_smoothing_gaussian_filter_stdev" : 5.0,
                        "half_window_size" : 400,
                        "bias" : 100,
                        "step_size" : 100
                    },
                    "remove_zeroed_lines" : {
                        "erosion_shape" : [
                            21,
                            1
                        ],
                        "dilation_shape" : [
                            1,
                            3
                        ]
                    },
                    "wavelet_transform" : {
                        "scale" : [
                            3,
                            4,
                            4
                        ]
                    }
                },
                "generate_dictionary" : {
                    "spams.trainDL" : {
                        "gamma2" : 0,
                        "gamma1" : 0,
                        "numThreads" : -1,
                        "K" : 10,
                        "iter" : 100,
                        "modeD" : 0,
                        "posAlpha" : True,
                        "clean" : True,
                        "posD" : True,
                        "batchsize" : 256,
                        "lambda1" : 0.2,
                        "lambda2" : 0,
                        "mode" : 2
                    }
                }
            }
        }

        self.config_blocks = {
            "generate_neurons_blocks" : {
                "num_processes" : 4,
                "block_shape" : [10000, -1, -1],
                "num_blocks" : [-1, 5, 5],
                "half_border_shape" : [0, 5, 5],
                "half_window_shape" : [50, 20, 20],

                "debug" : True,

                "generate_neurons" : {
                    "__comment__run_stage" : "Where to run until either preprocessing, dictionary, or postprocessing. If resume, is true then it will delete the previous results at this stage. By default (all can be set explicitly to null string)runs all the way through.",

                    "run_stage" : "all",

                    "__comment__normalize_data" : "These are arguments that will be passed to normalize_data.",

                    "preprocess_data" : {
                        "remove_zeroed_lines" : {
                            "erosion_shape" : [21, 1],
                            "dilation_shape" : [1, 3]
                        },

                        "extract_f0" : {
                            "bias" : 100,

                            "temporal_smoothing_gaussian_filter_stdev" : 5.0,

                            "half_window_size" : 50,          "__comment__window_size" : "In number of frames",
                            "step_size" : 100,                "__comment__step_size" : "In number of frames",
                            "which_quantile" : 0.5,           "__comment__which_quantile" : "Must be a single value (i.e. 0.5) to extract.",

                            "spatial_smoothing_gaussian_filter_stdev" : 5.0
                        },

                        "wavelet_transform" : {
                            "scale" : [3, 4, 4]
                        },

                        "normalize_data" : {
                            "simple_image_processing.renormalized_images": {
                                "ord" : 2
                            }
                        }
                    },


                    "__comment__generate_dictionary" : "These are arguments that will be passed to generate_dictionary.",

                    "generate_dictionary" : {
                        "spams.trainDL" : {
                            "K" : 10,
                            "gamma2": 0,
                            "gamma1": 0,
                            "numThreads": -1,
                            "batchsize": 256,
                            "iter": 100,
                            "lambda1": 0.2,
                            "posD": True,
                            "clean": True,
                            "modeD": 0,
                            "posAlpha": True,
                            "mode": 2,
                            "lambda2": 0
                        }
                    },


                    "postprocess_data" : {

                        "__comment__wavelet_denoising" : "These are arguments that will be passed to wavelet_denoising.",

                        "wavelet_denoising" : {

                            "denoising.estimate_noise" : {
                                "significance_threshhold" : 3.0
                            },

                            "denoising.significant_mask" : {
                                "noise_threshhold" : 3.0
                            },

                            "wavelet_transform.wavelet_transform" : {
                                "scale" : 4
                            },

                            "accepted_region_shape_constraints" : {
                                "major_axis_length" : {
                                    "min" : 0.0,
                                    "max" : 25.0
                                }
                            },

                            "remove_low_intensity_local_maxima" : {
                                "percentage_pixels_below_max" : 0

                            },

                            "__comment__min_local_max_distance" : 6.0,
                            "remove_too_close_local_maxima" : {
                                "min_local_max_distance"  : 100.0
                            },

                            "use_watershed" : True,

                            "__comment__accepted_neuron_shape_constraints_area_max" : 250,
                            "accepted_neuron_shape_constraints" : {
                                "area" : {
                                    "min" : 30,
                                    "max" : 600
                                },

                                "eccentricity" : {
                                    "min" : 0.0,
                                    "max" : 0.9
                                }
                            }
                        },


                        "merge_neuron_sets" : {
                            "alignment_min_threshold" : 0.6,
                            "overlap_min_threshold" : 0.6,

                            "fuse_neurons" : {
                                "fraction_mean_neuron_max_threshold" : 0.01
                            }
                        }
                    }
                }
            }
        }

        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir = os.path.abspath(self.temp_dir)

        self.hdf5_input_filename = os.path.join(self.temp_dir, "input.h5")
        self.hdf5_input_filepath = self.hdf5_input_filename + "/" + "images"
        self.hdf5_output_filename = os.path.join(self.temp_dir, "output.h5")
        self.hdf5_output_filepath = self.hdf5_output_filename + "/"

        self.config_a_block_filename = os.path.join(self.temp_dir, "config_a_block.json")
        self.config_blocks_filename = os.path.join(self.temp_dir, "config_blocks.json")

        self.space = numpy.array([110, 110])
        self.radii = numpy.array([7, 6, 6, 6, 7, 6])
        self.magnitudes = numpy.array([15, 16, 15, 17, 16, 16])
        self.points = numpy.array([[30, 24],
                                   [59, 65],
                                   [21, 65],
                                   [14, 14],
                                   [72, 16],
                                   [45, 32]])

        self.bases_indices = [[1, 3, 4], [0, 2], [5]]
        self.linspace_length = 25

        self.masks = synthetic_data.generate_hypersphere_masks(self.space, self.points, self.radii)
        self.images = synthetic_data.generate_gaussian_images(self.space, self.points, self.radii/3.0, self.magnitudes) * self.masks

        self.bases_masks = numpy.zeros((len(self.bases_indices),) + self.masks.shape[1:] , dtype=self.masks.dtype)
        self.bases_images = numpy.zeros((len(self.bases_indices),) + self.images.shape[1:] , dtype=self.images.dtype)

        for i, each_basis_indices in enumerate(self.bases_indices):
            self.bases_masks[i] = self.masks[list(each_basis_indices)].max(axis = 0)
            self.bases_images[i] = self.images[list(each_basis_indices)].max(axis = 0)

        self.image_stack = None
        ramp = numpy.concatenate([numpy.linspace(0, 1, self.linspace_length), numpy.linspace(1, 0, self.linspace_length)])

        self.image_stack = numpy.zeros((self.bases_images.shape[0] * len(ramp),) + self.bases_images.shape[1:],
                                       dtype = self.bases_images.dtype)
        for i in xrange(len(self.bases_images)):
            image_stack_slice = slice(i * len(ramp), (i+1) * len(ramp), 1)

            self.image_stack[image_stack_slice] = nanshe.expanded_numpy.all_permutations_operation(operator.mul,
                                                                                                   ramp,
                                                                                                   self.bases_images[i])

        print self.image_stack[self.image_stack.nonzero()]
        print self.image_stack.shape

        with h5py.File(self.hdf5_input_filename, "w") as fid:
            fid["images"] = self.image_stack

        with open(self.config_a_block_filename, "w") as fid:
            json.dump(self.config_a_block, fid)

        with open(self.config_blocks_filename, "w") as fid:
            json.dump(self.config_blocks, fid)

    def test_main_1(self):
        executable = os.path.splitext(nanshe.nanshe_learner.__file__)[0] + os.extsep + "py"

        argv = (executable, self.config_a_block_filename, self.hdf5_input_filepath, self.hdf5_output_filepath,)

        assert(0 == nanshe.nanshe_learner.main(*argv))

        assert(os.path.exists(self.hdf5_output_filename))

        with h5py.File(self.hdf5_output_filename, "r") as fid:
            assert("neurons" in fid)

            neurons = fid["neurons"].value

        assert(len(self.points) == len(neurons))

        neuron_maxes = (neurons["image"] == nanshe.expanded_numpy.expand_view(neurons["max_F"], neurons["image"].shape[1:]))
        neuron_max_points = numpy.array(neuron_maxes.max(axis = 0).nonzero()).T.copy()

        matched = dict()
        unmatched_points = numpy.arange(len(self.points))
        for i in xrange(len(neuron_max_points)):
            new_unmatched_points = []
            for j in unmatched_points:
                if not (neuron_max_points[i] == self.points[j]).all():
                    new_unmatched_points.append(j)
                else:
                    matched[i] = j

            unmatched_points = new_unmatched_points

        assert(len(unmatched_points) == 0)

    def test_main_2(self):
        executable = os.path.splitext(nanshe.nanshe_learner.__file__)[0] + os.extsep + "py"

        argv = (executable, self.config_blocks_filename, self.hdf5_input_filepath, self.hdf5_output_filepath,)

        assert(0 == nanshe.nanshe_learner.main(*argv))

        assert(os.path.exists(self.hdf5_output_filename))

        with h5py.File(self.hdf5_output_filename, "r") as fid:
            assert("neurons" in fid)

            neurons = fid["neurons"].value

        assert(len(self.points) == len(neurons))

        neuron_maxes = (neurons["image"] == nanshe.expanded_numpy.expand_view(neurons["max_F"], neurons["image"].shape[1:]))
        neuron_max_points = numpy.array(neuron_maxes.max(axis = 0).nonzero()).T.copy()

        matched = dict()
        unmatched_points = numpy.arange(len(self.points))
        for i in xrange(len(neuron_max_points)):
            new_unmatched_points = []
            for j in unmatched_points:
                if not (neuron_max_points[i] == self.points[j]).all():
                    new_unmatched_points.append(j)
                else:
                    matched[i] = j

            unmatched_points = new_unmatched_points

        assert(len(unmatched_points) == 0)

    def test_generate_neurons_io_handler_1(self):
        nanshe.nanshe_learner.generate_neurons_io_handler(self.hdf5_input_filepath, self.hdf5_output_filepath, self.config_a_block_filename)

        assert(os.path.exists(self.hdf5_output_filename))

        with h5py.File(self.hdf5_output_filename, "r") as fid:
            assert("neurons" in fid)

            neurons = fid["neurons"].value

        assert(len(self.points) == len(neurons))

        neuron_maxes = (neurons["image"] == nanshe.expanded_numpy.expand_view(neurons["max_F"], neurons["image"].shape[1:]))
        neuron_max_points = numpy.array(neuron_maxes.max(axis = 0).nonzero()).T.copy()

        matched = dict()
        unmatched_points = numpy.arange(len(self.points))
        for i in xrange(len(neuron_max_points)):
            new_unmatched_points = []
            for j in unmatched_points:
                if not (neuron_max_points[i] == self.points[j]).all():
                    new_unmatched_points.append(j)
                else:
                    matched[i] = j

            unmatched_points = new_unmatched_points

        assert(len(unmatched_points) == 0)

    def test_generate_neurons_io_handler_2(self):
        nanshe.nanshe_learner.generate_neurons_io_handler(self.hdf5_input_filepath, self.hdf5_output_filepath, self.config_blocks_filename)

        assert(os.path.exists(self.hdf5_output_filename))

        with h5py.File(self.hdf5_output_filename, "r") as fid:
            assert("neurons" in fid)

            neurons = fid["neurons"].value

        assert(len(self.points) == len(neurons))

        neuron_maxes = (neurons["image"] == nanshe.expanded_numpy.expand_view(neurons["max_F"], neurons["image"].shape[1:]))
        neuron_max_points = numpy.array(neuron_maxes.max(axis = 0).nonzero()).T.copy()

        matched = dict()
        unmatched_points = numpy.arange(len(self.points))
        for i in xrange(len(neuron_max_points)):
            new_unmatched_points = []
            for j in unmatched_points:
                if not (neuron_max_points[i] == self.points[j]).all():
                    new_unmatched_points.append(j)
                else:
                    matched[i] = j

            unmatched_points = new_unmatched_points

        assert(len(unmatched_points) == 0)

    def test_generate_neurons_a_block(self):
        nanshe.nanshe_learner.generate_neurons_a_block(self.hdf5_input_filepath, self.hdf5_output_filepath, **self.config_a_block)

        assert(os.path.exists(self.hdf5_output_filename))

        with h5py.File(self.hdf5_output_filename, "r") as fid:
            assert("neurons" in fid)

            neurons = fid["neurons"].value

        assert(len(self.points) == len(neurons))

        neuron_maxes = (neurons["image"] == nanshe.expanded_numpy.expand_view(neurons["max_F"], neurons["image"].shape[1:]))
        neuron_max_points = numpy.array(neuron_maxes.max(axis = 0).nonzero()).T.copy()

        matched = dict()
        unmatched_points = numpy.arange(len(self.points))
        for i in xrange(len(neuron_max_points)):
            new_unmatched_points = []
            for j in unmatched_points:
                if not (neuron_max_points[i] == self.points[j]).all():
                    new_unmatched_points.append(j)
                else:
                    matched[i] = j

            unmatched_points = new_unmatched_points

        assert(len(unmatched_points) == 0)

    def test_generate_neurons_blocks(self):
        nanshe.nanshe_learner.generate_neurons_blocks(self.hdf5_input_filepath, self.hdf5_output_filepath, **self.config_blocks["generate_neurons_blocks"])

        assert(os.path.exists(self.hdf5_output_filename))

        with h5py.File(self.hdf5_output_filename, "r") as fid:
            assert("neurons" in fid)

            neurons = fid["neurons"].value

        assert(len(self.points) == len(neurons))

        neuron_maxes = (neurons["image"] == nanshe.expanded_numpy.expand_view(neurons["max_F"], neurons["image"].shape[1:]))
        neuron_max_points = numpy.array(neuron_maxes.max(axis = 0).nonzero()).T.copy()

        matched = dict()
        unmatched_points = numpy.arange(len(self.points))
        for i in xrange(len(neuron_max_points)):
            new_unmatched_points = []
            for j in unmatched_points:
                if not (neuron_max_points[i] == self.points[j]).all():
                    new_unmatched_points.append(j)
                else:
                    matched[i] = j

            unmatched_points = new_unmatched_points

        assert(len(unmatched_points) == 0)

    def test_generate_neurons(self):
        with h5py.File(self.hdf5_output_filename, "a") as output_file_handle:
            output_group = output_file_handle["/"]

            # Get a debug logger for the HDF5 file (if needed)
            array_debug_recorder = nanshe.HDF5_recorder.generate_HDF5_array_recorder(output_group,
                group_name = "debug",
                enable = self.config_a_block["debug"],
                overwrite_group = False,
                recorder_constructor = nanshe.HDF5_recorder.HDF5EnumeratedArrayRecorder
            )

            # Saves intermediate result to make resuming easier
            resume_logger = nanshe.HDF5_recorder.generate_HDF5_array_recorder(output_group,
                recorder_constructor = nanshe.HDF5_recorder.HDF5ArrayRecorder,
                overwrite = True
            )

            nanshe.nanshe_learner.generate_neurons.resume_logger = resume_logger
            nanshe.nanshe_learner.generate_neurons.recorders.array_debug_recorder = array_debug_recorder
            nanshe.nanshe_learner.generate_neurons(self.image_stack, **self.config_a_block["generate_neurons"])

        assert(os.path.exists(self.hdf5_output_filename))

        with h5py.File(self.hdf5_output_filename, "r") as fid:
            assert("neurons" in fid)

            neurons = fid["neurons"].value

        assert(len(self.points) == len(neurons))

        neuron_maxes = (neurons["image"] == nanshe.expanded_numpy.expand_view(neurons["max_F"], neurons["image"].shape[1:]))
        neuron_max_points = numpy.array(neuron_maxes.max(axis = 0).nonzero()).T.copy()

        matched = dict()
        unmatched_points = numpy.arange(len(self.points))
        for i in xrange(len(neuron_max_points)):
            new_unmatched_points = []
            for j in unmatched_points:
                if not (neuron_max_points[i] == self.points[j]).all():
                    new_unmatched_points.append(j)
                else:
                    matched[i] = j

            unmatched_points = new_unmatched_points

        assert(len(unmatched_points) == 0)

    def teardown(self):
        try:
            os.remove(self.config_a_block_filename)
        except OSError:
            pass
        self.config_a_block_filename = ""

        try:
            os.remove(self.config_blocks_filename)
        except OSError:
            pass
        self.config_blocks_filename = ""

        try:
            os.remove(self.hdf5_input_filename)
        except OSError:
            pass
        self.hdf5_input_filename = ""

        try:
            os.remove(self.hdf5_output_filename)
        except OSError:
            pass
        self.hdf5_output_filename = ""

        shutil.rmtree(self.temp_dir)
        self.temp_dir = ""