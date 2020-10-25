module.exports = function(grunt) {
	const sass = require('node-sass');

	grunt.initConfig({
		watch: {
			options: {
				spawn: false
			},
			sass: {
				files: 'sass/*.scss',
				tasks: ['sass', 'postcss']
			}
		},
		postcss: {
			options: {
				processors: [
					require('autoprefixer')({
						browsers: [
							'last 2 versions',
							'ie 8',
							'ie 9'
						]
					}),
				]
			},
			dist: {
				src: 'dist/*.css'
			}
		},
		uglify: {
			options: {
				mangle: false,
				compress: true
			},
			dist: {
				files: [{
					expand: true,
					cwd: 'javascript',
					src: '**/*.js',
					dest: 'dist'
				}]
			}
		},
		cssmin: {
			target: {
				expand: true,
				cwd: 'dist',
				dest: 'dist',
				src: '**/*.css',
				ext: '.css'
			}
		},
		sass: {
			options: {
				implementation: sass,
				sourceMap: false
			},
			dist: {
				options: {
					style: 'expanded'
				},
				files: [{
					expand: true,
					cwd: "sass",
					src: ["**/*.scss"],
					dest: "dist",
					ext: ".css"
				}]
			}
		},
	});

	// Load dependencies
	grunt.loadNpmTasks('grunt-contrib-watch');
	grunt.loadNpmTasks('grunt-sass');
	grunt.loadNpmTasks('grunt-scss-lint');
	grunt.loadNpmTasks('grunt-postcss');
	grunt.loadNpmTasks('grunt-contrib-cssmin');
	grunt.loadNpmTasks('grunt-contrib-uglify');

	// Generate and format the CSS
	grunt.task.registerTask('default', [ 'watch' ]);
	grunt.task.registerTask('javascript', [ 'uglify' ]);
	grunt.task.registerTask('stylesheets', [
		'sass',
		'postcss',
		'cssmin'
	]);
};
