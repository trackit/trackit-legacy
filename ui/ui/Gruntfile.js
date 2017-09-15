/*global module:false*/
module.exports = function(grunt) {

    grunt.loadNpmTasks('grunt-include-source');
    grunt.loadNpmTasks('grunt-wiredep');
    grunt.loadNpmTasks('grunt-remove');
    grunt.loadNpmTasks('grunt-execute');
    // These plugins provide necessary tasks.
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-cssmin');
    grunt.loadNpmTasks('grunt-contrib-qunit');
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-protractor-webdriver');
    grunt.loadNpmTasks('grunt-protractor-runner');
    grunt.loadNpmTasks('grunt-babel');
    grunt.loadNpmTasks('grunt-contrib-watch');

    // Project configuration.
    grunt.initConfig({
        // Metadata.
        pkg: grunt.file.readJSON('package.json'),
        banner: '/*! <%= pkg.title || pkg.name %> - v<%= pkg.version %> - ' +
            '<%= grunt.template.today("yyyy-mm-dd") %>\n' +
            '<%= pkg.homepage ? "* " + pkg.homepage + "\\n" : "" %>' +
            '* Copyright (c) <%= grunt.template.today("yyyy") %> <%= pkg.author.name %>;' +
            ' Licensed <%= _.pluck(pkg.licenses, "type").join(", ") %> */\n',
        // Task configuration.
        includeSource: {
            options: {
                basePath: 'app',
                baseUrl: '/',
            },
            app: {
                files: {
                    'app/index.html': 'app/index.html.tpl'
                }
            },
            prod: {
                files: {
                    'app/index.html': 'app/index.prod.html.tpl'
                }
            }
        },
        execute: {
            server: {
                src: ['server.js']
            }
        },
        cssmin: {
            target: {
                files: [{
                    expand: true,
                    cwd: 'app/css',
                    src: ['*.css', '!*.min.css'],
                    dest: 'app/prodcss/',
                    ext: '.min.css'
                }]
            }
        },
        uglify: {
            options: {
                mangle: false
            },
            dist: {
                files: {
                    'app/min.js': ['app/app.js',
                        'app/components/**/*.js',
                        'app/components/**/**/*.js',
                        'app/directives/**/*.js',
                        'app/models/**/*.js',
                        'app/filters/**/*.js'
                    ]
                }
            }
        },
        concat: {
            cssprod: {
                src: ['app/prodcss/*.min.css'],
                dest: 'app/min.css'
            },
        },
        protractor_webdriver: {
            e2e: {
                options: {},
            },
        },
        protractor: {
            options: {
                configFile: "e2e-tests/protractor.conf.js", // Default config file
                keepAlive: false, // If false, the grunt process stops when the test fails.
                noColor: false, // If true, protractor will not use colors in its output.
                args: {
                    verbose: true,
                    baseUrl: "http://localhost:8000"
                }
            },
            all: {}
        },
        babel: {
            options: {
                sourceMap: true,
                presets: ['babel-preset-es2015', 'react']
            },
            dist: {
                files: {
                    'app/components/react/testComponent.js': 'app/react-src/testComponent.js',
                    'app/components/react/cloudMoverComponent.js': 'app/react-src/cloudMoverComponent.js',
                    'app/components/react/treeviewComponent.js': 'app/react-src/treeviewComponent.js',
                    'app/components/react/stateViewerComponent.js': 'app/react-src/stateViewerComponent.js',
                    'app/components/react/transfersViewerComponent.js': 'app/react-src/transfersViewerComponent.js',

                }
            }
        },
        wiredep: {
            task: {
                // Point to the files that should be updated when
                // you run `grunt wiredep`
                src: [
                    'app/index.html'
                ],
                fileTypes: {
                    html: {
                        replace: {
                            js: '<script src="/{{filePath}}"></script>',
                            css: '<link rel="stylesheet" href="/{{filePath}}" />'
                        }
                    }
                },
                options: {}
            }
        },
        remove: {
            options: {
                trace: true
            },
            fileList: ['app/index.html'],
            dirList: []
        },
        watch: {
            src: {
                files: 'app/react-src/*.js',
                tasks: ['build'],
                options: {
                    livereload: true,
                },
            },
        }
    });



    // Default task.
    grunt.registerTask('build', ['babel', 'remove', 'includeSource:app', 'wiredep']);

    grunt.registerTask('run', ['execute']);

    grunt.registerTask('test', ['protractor_webdriver', 'protractor']);

    grunt.registerTask('prod', ['babel', 'remove', 'cssmin', 'concat:cssprod', 'includeSource:prod', 'wiredep', 'uglify']);

};
