"""
Load initial benchmark definitions (BDL) for all age bands and modes.

This migration populates the BenchmarkVersion table with rubric definitions
for ages 8-18 across three modes: presenting, explaining, persuading.
"""

from django.db import migrations


def load_benchmark_definitions(apps, schema_editor):
    """Load comprehensive BDL definitions for all age bands and modes."""
    BenchmarkVersion = apps.get_model('benchmarks', 'BenchmarkVersion')
    User = apps.get_model('users', 'User')
    
    # Get or create a system user for the benchmarks
    system_user = User.objects.filter(role='admin').first()
    
    # Define age bands (UK year groups)
    age_bands = [
        ('8-9', 'Year 4'),
        ('9-10', 'Year 5'),
        ('10-11', 'Year 6'),
        ('11-12', 'Year 7'),
        ('12-13', 'Year 8'),
        ('13-14', 'Year 9'),
        ('14-15', 'Year 10'),
        ('15-16', 'Year 11'),
        ('16-17', 'Year 12'),
        ('17-18', 'Year 13'),
    ]
    
    modes = ['presenting', 'explaining', 'persuading']
    
    pk_counter = 1
    
    for age_band, year_group in age_bands:
        for mode in modes:
            # Get age-appropriate thresholds
            base_wpm_min, base_wpm_max = get_age_wpm_range(age_band)
            complexity_multiplier = get_complexity_multiplier(age_band)
            
            definition = create_benchmark_definition(
                age_band=age_band,
                year_group=year_group,
                mode=mode,
                base_wpm_min=base_wpm_min,
                base_wpm_max=base_wpm_max,
                complexity_multiplier=complexity_multiplier
            )
            
            BenchmarkVersion.objects.get_or_create(
                version='v1.0.0',
                age_band=age_band,
                mode=mode,
                defaults={
                    'definition': definition,
                    'is_active': True,
                    'created_by': system_user,
                    'notes': f'Initial benchmark for {year_group} ({age_band}) {mode} mode'
                }
            )
            pk_counter += 1


def get_age_wpm_range(age_band):
    """Return appropriate WPM range for age band."""
    ranges = {
        '8-9': (60, 100),
        '9-10': (70, 110),
        '10-11': (80, 120),
        '11-12': (90, 130),
        '12-13': (100, 140),
        '13-14': (110, 150),
        '14-15': (110, 160),
        '15-16': (120, 170),
        '16-17': (120, 170),
        '17-18': (120, 170),
    }
    return ranges.get(age_band, (80, 120))


def get_complexity_multiplier(age_band):
    """Return complexity expectation multiplier for age band."""
    multipliers = {
        '8-9': 0.6,
        '9-10': 0.7,
        '10-11': 0.8,
        '11-12': 0.9,
        '12-13': 1.0,
        '13-14': 1.1,
        '14-15': 1.2,
        '15-16': 1.3,
        '16-17': 1.4,
        '17-18': 1.5,
    }
    return multipliers.get(age_band, 1.0)


def create_benchmark_definition(age_band, year_group, mode, base_wpm_min, base_wpm_max, complexity_multiplier):
    """Create a complete benchmark definition for an age band and mode."""
    
    # Mode-specific descriptions and weights
    mode_configs = {
        'presenting': {
            'description': f'Presenting information to an audience - {year_group} level',
            'strand_weights': {'physical': 0.25, 'linguistic': 0.25, 'cognitive': 0.35, 'social_emotional': 0.15},
            'focus': 'audience_engagement'
        },
        'explaining': {
            'description': f'Explaining concepts and processes - {year_group} level',
            'strand_weights': {'physical': 0.20, 'linguistic': 0.25, 'cognitive': 0.40, 'social_emotional': 0.15},
            'focus': 'causal_reasoning'
        },
        'persuading': {
            'description': f'Making a case and convincing others - {year_group} level',
            'strand_weights': {'physical': 0.20, 'linguistic': 0.30, 'cognitive': 0.40, 'social_emotional': 0.10},
            'focus': 'argumentation'
        }
    }
    
    config = mode_configs[mode]
    
    return {
        'version': 'v1.0.0',
        'age_band': age_band,
        'mode': mode,
        'year_group': year_group,
        'description': config['description'],
        'strands': create_strands(mode, base_wpm_min, base_wpm_max, complexity_multiplier),
        'scoring_logic': {
            'minimum_evidence_clips': 3,
            'maximum_evidence_clips': 8,
            'confidence_threshold': 0.6,
            'strand_weights': config['strand_weights']
        },
        'evidence_rules': {
            'clip_duration_min': 5,
            'clip_duration_max': 30,
            'requires_diverse_strands': True,
            'max_clips_per_strand': 3
        },
        'feedback_templates': create_feedback_templates(mode, year_group),
        'eal_scaffolds': create_eal_scaffolds(mode, complexity_multiplier)
    }


def create_strands(mode, base_wpm_min, base_wpm_max, complexity_multiplier):
    """Create strand definitions with age-appropriate thresholds."""
    
    # Adjust thresholds by complexity
    wpm_emerging_max = int(base_wpm_min * 0.9)
    wpm_expected_min = base_wpm_min
    wpm_expected_max = base_wpm_max
    wpm_exceeding_min = int(base_wpm_max * 0.9)
    
    filler_emerging = int(8 / complexity_multiplier)
    filler_expected_max = int(5 / complexity_multiplier)
    filler_exceeding = int(2 / complexity_multiplier)
    
    vocab_emerging = 0.3 + (0.1 * complexity_multiplier)
    vocab_expected = 0.45 + (0.05 * complexity_multiplier)
    vocab_exceeding = 0.6 + (0.05 * complexity_multiplier)
    
    return {
        'physical': {
            'description': 'Physical delivery and voice control',
            'weight': 0.25,
            'subskills': {
                'voice_projection': {
                    'description': 'Speaking clearly and at appropriate volume',
                    'weight': 0.4,
                    'bands': {
                        'emerging': {
                            'descriptor': 'Voice often too quiet or unclear; difficult to hear',
                            'evidence_rules': [f'wpm < {wpm_emerging_max} OR volume_variance < 0.2'],
                            'signal_thresholds': {'max_wpm': wpm_emerging_max, 'min_volume_variance': 0.2}
                        },
                        'expected': {
                            'descriptor': 'Voice generally clear and audible throughout',
                            'evidence_rules': [f'wpm {wpm_expected_min}-{wpm_expected_max} AND volume_variance >= 0.2'],
                            'signal_thresholds': {'min_wpm': wpm_expected_min, 'max_wpm': wpm_expected_max}
                        },
                        'exceeding': {
                            'descriptor': 'Voice consistently clear with effective variation for emphasis',
                            'evidence_rules': [f'wpm >= {wpm_exceeding_min} AND volume_variance > 0.4'],
                            'signal_thresholds': {'min_wpm': wpm_exceeding_min, 'min_volume_variance': 0.4}
                        }
                    }
                },
                'pace_control': {
                    'description': 'Speaking at an appropriate and varied pace',
                    'weight': 0.35,
                    'bands': {
                        'emerging': {
                            'descriptor': 'Speaks too fast or too slow; rushes or has long uncomfortable pauses',
                            'evidence_rules': [f'wpm > {int(base_wpm_max * 1.2)} OR wpm < {int(base_wpm_min * 0.7)} OR pause_ratio > 0.4'],
                            'signal_thresholds': {'max_wpm': int(base_wpm_max * 1.2), 'min_wpm': int(base_wpm_min * 0.7)}
                        },
                        'expected': {
                            'descriptor': 'Generally appropriate pace with some variation',
                            'evidence_rules': [f'wpm {wpm_expected_min}-{wpm_expected_max} AND pause_ratio 0.15-0.35'],
                            'signal_thresholds': {'min_wpm': wpm_expected_min, 'max_wpm': wpm_expected_max}
                        },
                        'exceeding': {
                            'descriptor': 'Uses pace effectively; slows for key points, varies naturally',
                            'evidence_rules': [f'wpm {wpm_expected_min}-{int(base_wpm_max * 1.1)} AND speech_rate_variance > 0.3'],
                            'signal_thresholds': {'min_rate_variance': 0.3}
                        }
                    }
                },
                'clarity': {
                    'description': 'Clear articulation and minimal fillers',
                    'weight': 0.25,
                    'bands': {
                        'emerging': {
                            'descriptor': f'Many fillers (>{filler_emerging}/min) and unclear pronunciation',
                            'evidence_rules': [f'filler_frequency > {filler_emerging}'],
                            'signal_thresholds': {'max_fillers_per_min': filler_emerging}
                        },
                        'expected': {
                            'descriptor': f'Some fillers (up to {filler_expected_max}/min) but generally clear',
                            'evidence_rules': [f'filler_frequency {filler_exceeding}-{filler_expected_max}'],
                            'signal_thresholds': {'max_fillers_per_min': filler_expected_max}
                        },
                        'exceeding': {
                            'descriptor': f'Clear and articulate; minimal fillers (<{filler_exceeding}/min)',
                            'evidence_rules': [f'filler_frequency <= {filler_exceeding}'],
                            'signal_thresholds': {'max_fillers_per_min': filler_exceeding}
                        }
                    }
                }
            }
        },
        'linguistic': {
            'description': 'Language use, vocabulary, and expression',
            'weight': 0.25,
            'subskills': {
                'vocabulary_range': {
                    'description': 'Range and precision of vocabulary',
                    'weight': 0.4,
                    'bands': {
                        'emerging': {
                            'descriptor': 'Basic repetitive vocabulary; limited topic-specific words',
                            'evidence_rules': [f'vocabulary_diversity < {vocab_emerging:.2f}'],
                            'signal_thresholds': {'max_diversity': round(vocab_emerging, 2)}
                        },
                        'expected': {
                            'descriptor': 'Adequate vocabulary with some topic-specific and varied word choices',
                            'evidence_rules': [f'vocabulary_diversity {vocab_emerging:.2f}-{vocab_expected:.2f}'],
                            'signal_thresholds': {'min_diversity': round(vocab_emerging, 2), 'max_diversity': round(vocab_expected, 2)}
                        },
                        'exceeding': {
                            'descriptor': 'Rich, varied, and precise vocabulary appropriate to topic',
                            'evidence_rules': [f'vocabulary_diversity >= {vocab_exceeding:.2f}'],
                            'signal_thresholds': {'min_diversity': round(vocab_exceeding, 2)}
                        }
                    }
                },
                'sentence_structure': {
                    'description': 'Sentence complexity and variety',
                    'weight': 0.35,
                    'bands': {
                        'emerging': {
                            'descriptor': 'Simple sentences; limited variety',
                            'evidence_rules': ['sentence_length_mean < 6 OR sentence_length_variance < 2'],
                            'signal_thresholds': {'max_avg_length': 6, 'max_variance': 2}
                        },
                        'expected': {
                            'descriptor': 'Mix of simple and compound sentences; some variety',
                            'evidence_rules': ['sentence_length_mean 6-12 AND sentence_length_variance 2-8'],
                            'signal_thresholds': {'min_avg_length': 6, 'max_avg_length': 12}
                        },
                        'exceeding': {
                            'descriptor': 'Varied sentence structures including complex sentences',
                            'evidence_rules': ['sentence_length_mean > 10 AND sentence_length_variance > 6'],
                            'signal_thresholds': {'min_avg_length': 10, 'min_variance': 6}
                        }
                    }
                },
                'register': {
                    'description': 'Appropriate formality and style',
                    'weight': 0.25,
                    'bands': {
                        'emerging': {
                            'descriptor': 'Overly informal or inappropriate register',
                            'evidence_rules': ['register_formality < 0.3'],
                            'signal_thresholds': {'max_formality': 0.3}
                        },
                        'expected': {
                            'descriptor': 'Generally appropriate register with some consistency',
                            'evidence_rules': ['register_formality 0.3-0.6'],
                            'signal_thresholds': {'min_formality': 0.3, 'max_formality': 0.6}
                        },
                        'exceeding': {
                            'descriptor': 'Consistently appropriate register; effective style choices',
                            'evidence_rules': ['register_formality > 0.55'],
                            'signal_thresholds': {'min_formality': 0.55}
                        }
                    }
                }
            }
        },
        'cognitive': create_cognitive_strand(mode, complexity_multiplier),
        'social_emotional': create_social_emotional_strand(mode)
    }


def create_cognitive_strand(mode, complexity_multiplier):
    """Create cognitive strand based on mode."""
    
    # Adjust thresholds by complexity
    reason_emerging = 0.5 * complexity_multiplier
    reason_expected_max = 2.0 * complexity_multiplier
    reason_exceeding = 2.5 * complexity_multiplier
    
    base_structure = {
        'description': 'Thinking, reasoning and structure',
        'weight': 0.35,
        'subskills': {}
    }
    
    if mode == 'presenting':
        base_structure['subskills'] = {
            'content_structure': {
                'description': 'Clear beginning, middle and end',
                'weight': 0.35,
                'bands': {
                    'emerging': {
                        'descriptor': 'Little or no clear structure; ideas jump around',
                        'evidence_rules': ['has_introduction = false OR has_conclusion = false'],
                        'signal_thresholds': {'requires_intro': True, 'requires_conclusion': True}
                    },
                    'expected': {
                        'descriptor': 'Clear beginning and end; middle section mostly organised',
                        'evidence_rules': ['has_introduction = true AND has_conclusion = true'],
                        'signal_thresholds': {'requires_intro': True, 'requires_conclusion': True}
                    },
                    'exceeding': {
                        'descriptor': 'Well-structured throughout; clear signposting of sections',
                        'evidence_rules': ['has_introduction = true AND has_conclusion = true AND structure_completeness > 0.75'],
                        'signal_thresholds': {'min_structure_score': 0.75}
                    }
                }
            },
            'key_points': {
                'description': 'Identifying and developing key points',
                'weight': 0.35,
                'bands': {
                    'emerging': {
                        'descriptor': 'Points not clearly identified or developed',
                        'evidence_rules': [f'reason_density < {reason_emerging:.1f}'],
                        'signal_thresholds': {'max_reason_density': round(reason_emerging, 1)}
                    },
                    'expected': {
                        'descriptor': 'Main points identified with some development',
                        'evidence_rules': [f'reason_density {reason_emerging:.1f}-{reason_expected_max:.1f}'],
                        'signal_thresholds': {'min_reason_density': round(reason_emerging, 1)}
                    },
                    'exceeding': {
                        'descriptor': 'Clear main points with effective development and examples',
                        'evidence_rules': [f'reason_density >= {reason_exceeding:.1f}'],
                        'signal_thresholds': {'min_reason_density': round(reason_exceeding, 1)}
                    }
                }
            },
            'coherence': {
                'description': 'Ideas flow logically',
                'weight': 0.3,
                'bands': {
                    'emerging': {'descriptor': 'Ideas disjointed and hard to follow', 'evidence_rules': ['coherence_score < 0.4']},
                    'expected': {'descriptor': 'Ideas generally follow logically', 'evidence_rules': ['coherence_score 0.4-0.7']},
                    'exceeding': {'descriptor': 'Ideas flow smoothly with clear connections', 'evidence_rules': ['coherence_score > 0.7']}
                }
            }
        }
    elif mode == 'explaining':
        base_structure['subskills'] = {
            'step_sequence': {
                'description': 'Clear logical sequence',
                'weight': 0.4,
                'bands': {
                    'emerging': {'descriptor': 'Steps or ideas out of order', 'evidence_rules': ['structure_completeness < 0.4']},
                    'expected': {'descriptor': 'Logical sequence with clear steps', 'evidence_rules': ['structure_completeness 0.4-0.75']},
                    'exceeding': {'descriptor': 'Excellent sequencing with clear transitions', 'evidence_rules': ['structure_completeness > 0.75']}
                }
            },
            'causal_reasoning': {
                'description': 'Explaining causes and effects',
                'weight': 0.35,
                'bands': {
                    'emerging': {
                        'descriptor': 'States what happens but rarely why',
                        'evidence_rules': [f'reason_density < {reason_emerging:.1f}'],
                        'signal_thresholds': {'max_reason_density': round(reason_emerging, 1)}
                    },
                    'expected': {
                        'descriptor': 'Explains reasons using causal language',
                        'evidence_rules': [f'reason_density {reason_emerging:.1f}-{reason_expected_max:.1f}'],
                        'signal_thresholds': {'min_reason_density': round(reason_emerging, 1)}
                    },
                    'exceeding': {
                        'descriptor': 'Sophisticated causal explanations with multiple factors',
                        'evidence_rules': [f'reason_density >= {reason_exceeding:.1f} AND counterpoint_density > 0.3'],
                        'signal_thresholds': {'min_reason_density': round(reason_exceeding, 1)}
                    }
                }
            },
            'examples': {
                'description': 'Using examples to clarify',
                'weight': 0.25,
                'bands': {
                    'emerging': {'descriptor': 'Few or no examples', 'evidence_rules': ['evidence_density < 0.3']},
                    'expected': {'descriptor': 'Clear relevant examples', 'evidence_rules': ['evidence_density 0.3-0.8']},
                    'exceeding': {'descriptor': 'Well-chosen varied examples', 'evidence_rules': ['evidence_density > 0.8']}
                }
            }
        }
    else:  # persuading
        base_structure['subskills'] = {
            'argument_structure': {
                'description': 'Clear claim with reasons and evidence',
                'weight': 0.4,
                'bands': {
                    'emerging': {
                        'descriptor': 'Claim unclear or unsupported',
                        'evidence_rules': ['has_introduction = false OR reason_density < 1.0'],
                        'signal_thresholds': {'min_reason_density': 1.0}
                    },
                    'expected': {
                        'descriptor': 'Clear claim with supporting reasons',
                        'evidence_rules': ['has_introduction = true AND reason_density >= 1.0'],
                        'signal_thresholds': {'min_reason_density': 1.0}
                    },
                    'exceeding': {
                        'descriptor': 'Strong claim with well-developed argument and evidence',
                        'evidence_rules': ['reason_density > 2.0 AND evidence_density > 0.5'],
                        'signal_thresholds': {'min_reason_density': 2.0, 'min_evidence_density': 0.5}
                    }
                }
            },
            'counter_arguments': {
                'description': 'Acknowledging other viewpoints',
                'weight': 0.3,
                'bands': {
                    'emerging': {'descriptor': 'Ignores other viewpoints', 'evidence_rules': ['counterpoint_density < 0.1']},
                    'expected': {'descriptor': 'May mention other views briefly', 'evidence_rules': ['counterpoint_density 0.1-0.4']},
                    'exceeding': {'descriptor': 'Addresses counter-arguments effectively', 'evidence_rules': ['counterpoint_density > 0.4']}
                }
            },
            'persuasive_techniques': {
                'description': 'Using language to persuade',
                'weight': 0.3,
                'bands': {
                    'emerging': {'descriptor': 'Limited persuasive language', 'evidence_rules': ['evidence_density < 0.3']},
                    'expected': {'descriptor': 'Some persuasive techniques used', 'evidence_rules': ['evidence_density 0.3-0.8']},
                    'exceeding': {'descriptor': 'Effective varied persuasive techniques', 'evidence_rules': ['evidence_density > 0.8']}
                }
            }
        }
    
    return base_structure


def create_social_emotional_strand(mode):
    """Create social-emotional strand based on mode."""
    
    base_structure = {
        'description': 'Audience awareness and engagement',
        'weight': 0.15,
        'subskills': {}
    }
    
    if mode == 'presenting':
        base_structure['subskills'] = {
            'audience_connection': {
                'description': 'Connecting with the audience',
                'weight': 0.5,
                'bands': {
                    'emerging': {'descriptor': 'Little awareness of audience', 'evidence_rules': ['audience_reference_frequency < 0.1']},
                    'expected': {'descriptor': 'Some audience awareness and connection', 'evidence_rules': ['audience_reference_frequency 0.1-0.3']},
                    'exceeding': {'descriptor': 'Strong audience connection throughout', 'evidence_rules': ['audience_reference_frequency > 0.3']}
                }
            },
            'confidence': {
                'description': 'Appearing confident and engaged',
                'weight': 0.5,
                'bands': {
                    'emerging': {'descriptor': 'Appears nervous or disengaged', 'evidence_rules': ['confidence_score < 0.3']},
                    'expected': {'descriptor': 'Reasonably confident', 'evidence_rules': ['confidence_score 0.3-0.65']},
                    'exceeding': {'descriptor': 'Confident and engaging', 'evidence_rules': ['confidence_score > 0.65']}
                }
            }
        }
    elif mode == 'explaining':
        base_structure['subskills'] = {
            'clarity_for_listener': {
                'description': 'Ensuring listener understands',
                'weight': 0.6,
                'bands': {
                    'emerging': {'descriptor': "Doesn't check understanding", 'evidence_rules': ['audience_reference_frequency < 0.1']},
                    'expected': {'descriptor': 'Some checking of understanding', 'evidence_rules': ['audience_reference_frequency 0.1-0.3']},
                    'exceeding': {'descriptor': 'Actively ensures understanding', 'evidence_rules': ['audience_reference_frequency > 0.3']}
                }
            },
            'patience': {
                'description': 'Taking time to explain properly',
                'weight': 0.4,
                'bands': {
                    'emerging': {'descriptor': 'Rushes through', 'evidence_rules': ['wpm > 150']},
                    'expected': {'descriptor': 'Appropriate pace', 'evidence_rules': ['wpm 80-140']},
                    'exceeding': {'descriptor': 'Patient, allows time to process', 'evidence_rules': ['wpm 80-130 AND pause_ratio > 0.2']}
                }
            }
        }
    else:  # persuading
        base_structure['subskills'] = {
            'audience_consideration': {
                'description': 'Adapting to audience concerns',
                'weight': 0.5,
                'bands': {
                    'emerging': {'descriptor': 'Ignores audience perspective', 'evidence_rules': ['audience_reference_frequency < 0.15']},
                    'expected': {'descriptor': 'Considers audience viewpoint', 'evidence_rules': ['audience_reference_frequency 0.15-0.4']},
                    'exceeding': {'descriptor': 'Skilfully addresses audience concerns', 'evidence_rules': ['audience_reference_frequency > 0.4']}
                }
            },
            'conviction': {
                'description': 'Conveying belief in position',
                'weight': 0.5,
                'bands': {
                    'emerging': {'descriptor': 'Appears uncertain', 'evidence_rules': ['confidence_score < 0.35 OR sentiment_compound < 0']},
                    'expected': {'descriptor': 'Shows some conviction', 'evidence_rules': ['confidence_score 0.35-0.7']},
                    'exceeding': {'descriptor': 'Strong authentic conviction', 'evidence_rules': ['confidence_score > 0.7 AND sentiment_compound > 0.2']}
                }
            }
        }
    
    return base_structure


def create_feedback_templates(mode, year_group):
    """Create mode-specific feedback templates."""
    
    templates = {
        'presenting': {
            'strengths': [
                "You spoke clearly so everyone could hear your ideas",
                "You had a clear beginning that told us what to expect",
                "You organised your ideas in a logical way",
                "You used interesting vocabulary to describe your topic",
                "You gave examples that helped us understand your points",
                "You appeared confident when presenting to the group",
                "You made good eye contact with your audience",
                "You used your voice effectively to emphasise key points"
            ],
            'next_steps': [
                "Try to speak a bit louder so everyone can hear you clearly",
                "Remember to pause and look at your audience, not just your notes",
                "Try to slow down a little - take your time with important points",
                "Use words like 'first', 'next', 'finally' to help us follow your ideas",
                "Try to give a reason or example for each of your main points",
                "Practise speaking without too many 'um' or 'like' fillers",
                "Work on having a clear ending that sums up your main points",
                "Try to make more eye contact with different parts of the room"
            ],
            'goals': [
                "Speak clearly and at the right volume for the whole room to hear",
                "Use connecting words (first, next, finally) to organise your ideas",
                "Give at least one example or reason for each main point you make",
                "Pause and make eye contact with different parts of the audience"
            ]
        },
        'explaining': {
            'strengths': [
                "You explained the steps in a clear and logical order",
                "You used 'because' and other words to explain why things happen",
                "Your examples helped me understand the concept better",
                "You spoke clearly and at a good pace for understanding",
                "You checked that your explanation made sense",
                "You broke down complex ideas into manageable parts",
                "You used clear language that matched your audience's level"
            ],
            'next_steps': [
                "Use sequence words (first, then, next, finally) to show the order clearly",
                "Remember to explain why something happens, not just what happens",
                "Give concrete examples to help your listener understand abstract ideas",
                "Check that your listener understands by asking questions",
                "Take your time with difficult concepts - don't rush",
                "Use comparisons to things your audience already knows",
                "Make sure your explanation has a clear beginning and end"
            ],
            'goals': [
                "Use clear sequence words when explaining steps or processes",
                "Always give at least one 'because' reason for each explanation",
                "Include helpful examples that your listener can relate to",
                "Check understanding by asking 'Does that make sense?'"
            ]
        },
        'persuading': {
            'strengths': [
                "You stated your position clearly from the beginning",
                "You gave strong reasons to support your argument",
                "You used persuasive language effectively",
                "You considered the audience's perspective",
                "You addressed potential counter-arguments",
                "You used evidence and examples to back up your points",
                "Your conclusion reinforced your main argument effectively"
            ],
            'next_steps': [
                "Make your main claim or position even clearer at the start",
                "Develop each reason with specific examples or evidence",
                "Use persuasive techniques like rhetorical questions or emotive language",
                "Consider what the other side might say and address those points",
                "Connect your argument to your audience's values or concerns",
                "End with a strong summary of why your position is the best one",
                "Use connecting words (furthermore, moreover, therefore) to strengthen your case"
            ],
            'goals': [
                "State a clear position and stick to it throughout",
                "Give at least three strong reasons with supporting evidence",
                "Address at least one counter-argument",
                "Use persuasive language to strengthen your case"
            ]
        }
    }
    
    return templates[mode]


def create_eal_scaffolds(mode, complexity_multiplier):
    """Create EAL scaffolds based on mode and age."""
    
    # Adjust scaffold complexity based on age
    if complexity_multiplier < 0.8:
        stem_complexity = 'simple'
    elif complexity_multiplier < 1.2:
        stem_complexity = 'intermediate'
    else:
        stem_complexity = 'advanced'
    
    scaffolds = {
        'presenting': {
            'simple': {
                'sentence_stems': [
                    "Today I am going to tell you about...",
                    "The first thing is...",
                    "Another important thing is...",
                    "For example...",
                    "In conclusion...",
                    "Thank you for listening"
                ],
                'planning_frames': [
                    "Opening: Say what you'll talk about",
                    "Point 1: First important thing + example",
                    "Point 2: Second important thing + example",
                    "Closing: Summarise what you said"
                ],
                'vocabulary_supports': [
                    "first", "second", "next", "then", "finally",
                    "for example", "because", "also", "important", "another"
                ]
            },
            'intermediate': {
                'sentence_stems': [
                    "Today I will be discussing...",
                    "My first point is...",
                    "Furthermore...",
                    "To illustrate this...",
                    "In summary...",
                    "To conclude..."
                ],
                'planning_frames': [
                    "Introduction: Hook + thesis statement",
                    "Body Paragraph 1: Point + Evidence + Example",
                    "Body Paragraph 2: Point + Evidence + Example",
                    "Conclusion: Restate main points + closing thought"
                ],
                'vocabulary_supports': [
                    "furthermore", "moreover", "however", "therefore",
                    "to illustrate", "for instance", "significantly", "consequently"
                ]
            },
            'advanced': {
                'sentence_stems': [
                    "I would like to begin by exploring...",
                    "A significant aspect of this is...",
                    "It is worth noting that...",
                    "This is exemplified by...",
                    "Taking these points into consideration...",
                    "In light of the evidence presented..."
                ],
                'planning_frames': [
                    "Introduction: Context + thesis + roadmap",
                    "Main Argument 1: Claim + Evidence + Analysis",
                    "Main Argument 2: Claim + Evidence + Analysis",
                    "Main Argument 3: Claim + Evidence + Analysis",
                    "Conclusion: Synthesis + implications + closing"
                ],
                'vocabulary_supports': [
                    "significantly", "fundamentally", "consequently", "nevertheless",
                    "paradoxically", "demonstrates", "illustrates", "underscores"
                ]
            }
        },
        'explaining': {
            'simple': {
                'sentence_stems': [
                    "First...", "Then...", "Next...", "After that...", "Finally...",
                    "This happens because...", "The reason is...",
                    "For example...", "This means..."
                ],
                'planning_frames': [
                    "What is being explained:",
                    "Step 1:", "Step 2:", "Step 3:",
                    "Why this happens:",
                    "Example:"
                ],
                'vocabulary_supports': [
                    "first", "then", "next", "because", "so", "this means", "for example"
                ]
            },
            'intermediate': {
                'sentence_stems': [
                    "The process begins when...",
                    "Following this...",
                    "As a result...",
                    "This occurs because...",
                    "To put it another way...",
                    "A clear example of this is..."
                ],
                'planning_frames': [
                    "Concept/Process Overview",
                    "Step-by-step explanation:",
                    "Cause and effect relationships:",
                    "Concrete examples:",
                    "Summary"
                ],
                'vocabulary_supports': [
                    "consequently", "as a result", "this leads to", "due to",
                    "the process involves", "subsequently", "thereby"
                ]
            },
            'advanced': {
                'sentence_stems': [
                    "The fundamental principle underlying this is...",
                    "This phenomenon occurs as a result of...",
                    "It is important to note that...",
                    "This can be understood by examining...",
                    "A pertinent example that illustrates this is...",
                    "In essence, this demonstrates that..."
                ],
                'planning_frames': [
                    "Concept Definition and Context",
                    "Mechanism/Process Analysis",
                    "Causal Relationships and Evidence",
                    "Illustrative Examples",
                    "Synthesis and Implications"
                ],
                'vocabulary_supports': [
                    "fundamentally", "inherently", "consequently", "manifests as",
                    "underpinned by", "gives rise to", "is characterized by"
                ]
            }
        },
        'persuading': {
            'simple': {
                'sentence_stems': [
                    "I believe that...",
                    "The first reason is...",
                    "Another reason is...",
                    "For example...",
                    "In conclusion...",
                    "That is why..."
                ],
                'planning_frames': [
                    "My opinion:",
                    "Reason 1:", "Reason 2:", "Reason 3:",
                    "Evidence/Examples:",
                    "Conclusion:"
                ],
                'vocabulary_supports': [
                    "I believe", "because", "therefore", "for example",
                    "importantly", "clearly", "obviously", "definitely"
                ]
            },
            'intermediate': {
                'sentence_stems': [
                    "It is clear that...",
                    "The primary argument for this is...",
                    "Furthermore...",
                    "This is supported by...",
                    "However, one might argue...",
                    "In conclusion, it is evident that..."
                ],
                'planning_frames': [
                    "Position Statement",
                    "Argument 1: Claim + Evidence",
                    "Argument 2: Claim + Evidence",
                    "Counter-argument and Response",
                    "Concluding Statement"
                ],
                'vocabulary_supports': [
                    "evidently", "furthermore", "conversely", "consequently",
                    "demonstrates", "undermines", "validates", "necessarily"
                ]
            },
            'advanced': {
                'sentence_stems': [
                    "There is compelling evidence that...",
                    "A fundamental argument supporting this position is...",
                    "Moreover, it is significant that...",
                    "This is corroborated by...",
                    "While it could be argued that...",
                    "Ultimately, the weight of evidence suggests..."
                ],
                'planning_frames': [
                    "Thesis and Context",
                    "Primary Argument: Assertion + Evidence + Analysis",
                    "Secondary Argument: Assertion + Evidence + Analysis",
                    "Counter-argument Acknowledgment and Refutation",
                    "Synthesis and Call to Action"
                ],
                'vocabulary_supports': [
                    "compelling", "fundamentally", "corroborates", "undermines",
                    "prima facie", "cogent", "ipso facto", "presupposes"
                ]
            }
        }
    }
    
    mode_scaffolds = scaffolds[mode][stem_complexity]
    return {
        'sentence_stems': mode_scaffolds['sentence_stems'],
        'planning_frames': mode_scaffolds['planning_frames'],
        'vocabulary_supports': mode_scaffolds['vocabulary_supports'],
        'complexity_level': stem_complexity
    }


def unload_benchmark_definitions(apps, schema_editor):
    """Remove loaded benchmark definitions."""
    BenchmarkVersion = apps.get_model('benchmarks', 'BenchmarkVersion')
    BenchmarkVersion.objects.filter(version='v1.0.0').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('benchmarks', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(load_benchmark_definitions, unload_benchmark_definitions),
    ]
