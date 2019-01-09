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
			},
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
				src: 'css/*.css'
			}
		},
		sass: {
			options: {
				implementation: sass,
				sourceMap: false
			},
			dist: {
				files: [{
					expand: true,
					cwd: "sass",
					src: ["**/*.scss"],
					dest: "css",
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

	// Generate and format the CSS
	grunt.registerTask('default', ['watch']);
};
