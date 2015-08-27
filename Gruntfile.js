module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    concat: {
      dist: {
        src: ['coffelli/static/coffelli/js/coffelli.js', 'coffelli/static/coffelli/js/jquery*.js'],
        dest: 'coffelli/static/coffelli/js/coffelli.min.js'
      }
    },
    jshint: {
      options: {
        "expr": true,
        "scripturl": true,
      },
      beforeconcat: ['coffelli/static/coffelli/js/coffelli.js', 'coffelli/static/coffelli/js/jquery*.js'],
      afterconcat: ['coffelli/static/coffelli/js/coffelli.min.js']
    },
    uglify: {
      build: {
        files: {
          'coffelli/static/coffelli/js/coffelli.min.js': ['coffelli/static/coffelli/js/coffelli.min.js']
        }
      }
    },
    compass: {
      dist: {
        options: {
          config: 'coffelli/compass/config.rb',
          sassDir: 'coffelli/compass/sass',
          cssDir: 'coffelli/static/coffelli/stylesheets',
          imagesDir: 'coffelli/static/coffelli/images',
          javascriptsDir: 'coffelli/static/coffelli/javascripts',
          outputStyle: 'compressed',
          relativeAssets: true,
          noLineComments: true
        }
      }
    },
    exec: {
      build_sphinx: {
        cmd: 'sphinx-build -b html docs docs/_build'
      }
    },
    flake8: {
      options: {
        maxLineLength: 200,
        format: 'pylint',
        showSource: true,
        ignore: ['E501']
      },
      src: ['setup.py', 'coffelli/**/*.py'],
    },
    watch: {
      js: {
          files: ['coffelli/static/coffelli/js/coffelli.js', 'coffelli/static/coffelli/js/jquery*.js'],
          tasks: ['jshint:beforeconcat', 'concat', 'jshint:afterconcat', 'uglify']
      },
      css: {
          files: ['coffelli/compass/sass/**/*.scss'],
          tasks: ['compass']
      },
      sphinx: {
        files: ['docs/*.rst', 'docs/*.py'],
        tasks: ['exec:build_sphinx']
      },
    },
  });

  // Load
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-compass');
  grunt.loadNpmTasks('grunt-exec');
  grunt.loadNpmTasks('grunt-flake8');

  // Javascripts
  grunt.registerTask('javascripts', 'JSHint, Concat and Uglify.', function() {
    grunt.task.run(['jshint:beforeconcat', 'concat', 'jshint:afterconcat', 'uglify']);
  });

  // Sphinx
  grunt.registerTask('sphinx', 'Build doc files.', function() {
    grunt.task.run(['exec:build_sphinx']);
  });

  // Default
  grunt.registerTask('default', ['watch']);

};
